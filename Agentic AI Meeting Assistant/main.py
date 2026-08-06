from datetime import date

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from langgraph.types import Command
from pydantic import BaseModel, Field

from src.graph import graph
from src.durable_workflow import dispatch_approved_candidates, persist_candidates, review_candidate
from src.insforge_client import InsForgeConfigurationError, InsForgeRepository
from src.media import MediaConfigurationError
from src.media_workflow import confirm_upload, create_upload, transcribe_media
from src.state import AgentState

load_dotenv()

app = FastAPI(title="Agentic AI Meeting Assistant")


class IngestRequest(BaseModel):
    transcript: str
    meeting_date: str
    meeting_id: str | None = None


class MediaUploadRequest(BaseModel):
    title: str = "Untitled meeting"
    meeting_date: date
    filename: str
    content_type: str
    size_bytes: int


class ReviewDecision(BaseModel):
    decision: str = Field(pattern="^(approve|reject|re_extract)$")
    approved_items: list[dict] = Field(default_factory=list)
    note: str = ""


class ReviewRequest(BaseModel):
    thread_id: str
    decision: ReviewDecision


class CandidateReviewRequest(BaseModel):
    reviewer_name: str = Field(min_length=1, max_length=200)
    decision: str = Field(pattern="^(APPROVED|EDITED|REJECTED|REEXTRACTION_REQUESTED)$")
    note: str = ""
    final_title: str | None = Field(default=None, max_length=500)
    priority: str | None = Field(default=None, pattern="^(HIGH|MEDIUM|LOW)$")
    resolved_due_date: str | None = None
    github_assignee_login: str | None = Field(default=None, max_length=100)
    final_owner_name: str | None = Field(default=None, max_length=200)


@app.post("/ingest")
def ingest(req: IngestRequest):
    """Extract candidates then pause at the native LangGraph review interrupt."""
    state: AgentState = {
        "transcript": req.transcript,
        "meeting_date": req.meeting_date,
        "meeting_id": req.meeting_id or req.meeting_date,
        "approved_items": [],
        "rejected_items": [],
        "action_hashes": [],
        "execution_results": [],
    }
    config = {"configurable": {"thread_id": req.meeting_id or req.meeting_date}}
    thread_id = config["configurable"]["thread_id"]
    graph.invoke(state, config)
    snapshot = graph.get_state(config)
    interrupt_payload = None
    if snapshot and snapshot.tasks and len(snapshot.tasks) > 0 and snapshot.tasks[0].interrupts:
        interrupt_payload = snapshot.tasks[0].interrupts[0].value

    if interrupt_payload is None:
        extracted = snapshot.values.get("extracted") if snapshot else None
        err = snapshot.values.get("error") if snapshot else None
        if extracted is not None and getattr(extracted, "executive_summary", "").startswith("Extraction failed"):
            err = extracted.executive_summary
        return {
            "status": "extraction_failed",
            "thread_id": thread_id,
            "error": err or "Extraction did not produce reviewable candidates.",
        }
    return {"status": "waiting_for_review", "thread_id": thread_id, "review": interrupt_payload}


@app.post("/review")
def review(req: ReviewRequest):
    """Resume a paused workflow. Only reviewer-supplied approved items can dispatch."""
    config = {"configurable": {"thread_id": req.thread_id}}
    result = graph.invoke(Command(resume=req.decision.model_dump()), config)
    return {"status": "completed", "thread_id": req.thread_id, "result": result}


def _media_error(error: Exception) -> HTTPException:
    if isinstance(error, (MediaConfigurationError, InsForgeConfigurationError)):
        return HTTPException(status_code=503, detail=str(error))
    if isinstance(error, LookupError):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, ValueError):
        return HTTPException(status_code=422, detail=str(error))
    return HTTPException(status_code=502, detail="Media processing failed. Check server logs for the provider error.")


def _start_media_review(media: dict, transcript: str) -> dict | None:
    """Immediately hand a completed transcript to the LangGraph review gate."""
    repository = InsForgeRepository()
    meeting = repository.get_one("meetings", media["meeting_id"])
    if not meeting:
        raise LookupError("Meeting metadata not found for this media file.")
    thread_id = f"meeting-{meeting['id']}"
    config = {"configurable": {"thread_id": thread_id}}
    graph.invoke({
        "transcript": transcript,
        "meeting_date": str(meeting["meeting_date"]),
        "meeting_id": meeting["meeting_key"],
        "media_id": media["id"],
        "approved_items": [],
        "rejected_items": [],
        "action_hashes": [],
        "execution_results": [],
    }, config)
    snapshot = graph.get_state(config)
    repository.update("meetings", meeting["id"], {"processing_status": "AWAITING_REVIEW"})
    if snapshot and snapshot.tasks and len(snapshot.tasks) > 0 and snapshot.tasks[0].interrupts:
        extracted = snapshot.values.get("extracted")
        candidates = persist_candidates(repository, meeting["id"], thread_id, extracted.action_items if extracted else [])
        payload = dict(snapshot.tasks[0].interrupts[0].value)
        payload["items"] = candidates
        return {"thread_id": thread_id, "payload": payload}
    # Either extraction failed or the graph ended without a review interrupt.
    # Surface a descriptive error to the caller instead of returning payload=None silently.
    extracted = snapshot.values.get("extracted") if snapshot else None
    err_detail = None
    if extracted is not None and getattr(extracted, "executive_summary", "").startswith("Extraction failed"):
        err_detail = extracted.executive_summary
    raise RuntimeError(
        err_detail or "Extraction did not produce any reviewable candidates. Check that the transcript is long enough and Groq credentials are configured."
    )


@app.post("/media/uploads")
def prepare_media_upload(req: MediaUploadRequest):
    """Create private GCS upload instructions and durable InsForge metadata."""
    try:
        result = create_upload(req.title, req.meeting_date, req.filename, req.content_type, req.size_bytes)
        return {
            "meeting_id": result["meeting"]["id"],
            "meeting_key": result["meeting"]["meeting_key"],
            "media_id": result["media"]["id"],
            "upload_url": result["upload_url"],
            "upload_method": "PUT",
            "required_headers": {"Content-Type": req.content_type},
        }
    except Exception as error:
        raise _media_error(error) from error


@app.post("/media/{media_id}/confirm-upload")
def mark_media_uploaded(media_id: str):
    try:
        return confirm_upload(media_id)
    except Exception as error:
        raise _media_error(error) from error


@app.post("/media/{media_id}/transcribe")
def start_transcription(media_id: str):
    """Transcribe a confirmed private GCS object and persist timestamp evidence."""
    try:
        media, transcription = transcribe_media(media_id)
        review = _start_media_review(media, transcription.text)
        return {
            "media_id": media_id,
            "meeting_id": media["meeting_id"],
            "transcript_characters": len(transcription.text),
            "segments": len(transcription.segments),
            "status": "awaiting_review",
            "review": review,
        }
    except Exception as error:
        raise _media_error(error) from error


@app.post("/meetings/{meeting_id}/action-items/{action_item_id}/review")
def review_action_item(meeting_id: str, action_item_id: str, req: CandidateReviewRequest):
    """Persist an individual reviewer decision before any GitHub dispatch is possible."""
    try:
        return review_candidate(
            InsForgeRepository(),
            meeting_id,
            action_item_id,
            reviewer_name=req.reviewer_name,
            decision=req.decision,
            note=req.note,
            final_title=req.final_title,
            priority=req.priority,
            resolved_due_date=req.resolved_due_date,
            github_assignee_login=req.github_assignee_login,
            final_owner_name=req.final_owner_name,
        )
    except Exception as error:
        raise _media_error(error) from error


@app.post("/meetings/{meeting_id}/dispatch")
def dispatch_meeting_candidates(meeting_id: str):
    """Create only reviewer-approved eligible GitHub issues; dry run is the default."""
    try:
        return {"results": dispatch_approved_candidates(InsForgeRepository(), meeting_id)}
    except Exception as error:
        raise _media_error(error) from error


@app.get("/health")
def health():
    return {"status": "ok"}
