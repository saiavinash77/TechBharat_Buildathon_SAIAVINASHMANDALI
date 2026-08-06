from datetime import date
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from langgraph.types import Command
from pydantic import BaseModel, Field

from src.graph import graph
from src.durable_workflow import dispatch_approved_candidates, persist_candidates, review_candidate
from src.ingest_workflow import create_text_meeting, run_extraction_review
from src.insforge_client import InsForgeConfigurationError, InsForgeRepository
from src.media import MediaConfigurationError, GCSMediaStore
from src.media_workflow import confirm_upload, create_upload, transcribe_media
from src.state import AgentState
from src.transcript_parser import parse_transcript_file

load_dotenv()

app = FastAPI(title="Agentic AI Meeting Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class IngestRequest(BaseModel):
    transcript: str
    meeting_date: str
    title: str = "Text transcript meeting"
    meeting_id: str | None = None


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


class MediaUploadRequest(BaseModel):
    title: str = "Untitled meeting"
    meeting_date: date
    filename: str
    content_type: str
    size_bytes: int


def _media_error(error: Exception) -> HTTPException:
    if isinstance(error, (MediaConfigurationError, InsForgeConfigurationError)):
        return HTTPException(status_code=503, detail=str(error))
    if isinstance(error, LookupError):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, ValueError):
        return HTTPException(status_code=422, detail=str(error))
    return HTTPException(status_code=502, detail=str(error))


def _enrich_review_payload(payload: dict, extracted) -> dict:
    if extracted:
        payload["decisions"] = extracted.decisions_made
        payload["open_questions"] = extracted.open_questions
        payload["risks_or_blockers"] = getattr(extracted, "risks_or_blockers", [])
    return payload


def _start_media_review(media: dict, transcript: str) -> dict:
    """Run extraction and persist durable candidates for media meetings."""
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
    repository.update("meetings", meeting["id"], {"processing_status": "AWAITING_REVIEW", "transcript_text": transcript})

    if not (snapshot and snapshot.tasks and snapshot.tasks[0].interrupts):
        extracted = snapshot.values.get("extracted") if snapshot else None
        err_detail = None
        if extracted is not None and getattr(extracted, "executive_summary", "").startswith("Extraction failed"):
            err_detail = extracted.executive_summary
        raise RuntimeError(err_detail or "Extraction did not produce reviewable candidates.")

    extracted = snapshot.values.get("extracted")
    candidates = persist_candidates(repository, meeting["id"], thread_id, extracted.action_items if extracted else [])
    payload = _enrich_review_payload(dict(snapshot.tasks[0].interrupts[0].value), extracted)
    payload["items"] = candidates
    return {"thread_id": thread_id, "payload": payload}


@app.get("/")
def root():
    return RedirectResponse(url="/ui")


@app.post("/ingest")
def ingest(req: IngestRequest):
    """Ingest plain-text transcript through the unified durable review pipeline."""
    try:
        meeting_date = date.fromisoformat(req.meeting_date)
        meeting = create_text_meeting(req.title, meeting_date, req.transcript)
        result = run_extraction_review(meeting, req.transcript)
        return {"status": "awaiting_review", **result}
    except Exception as error:
        raise _media_error(error) from error


@app.post("/ingest/file")
async def ingest_transcript_file(file: UploadFile = File(...)):
    """Ingest .txt, .vtt, or .srt transcript files."""
    try:
        content = await file.read()
        filename = Path(file.filename or "transcript.txt").name
        transcript = parse_transcript_file(content, filename)
        if len(transcript.strip()) < 50:
            raise ValueError("Transcript too short after parsing. Need at least 50 characters.")
        meeting = create_text_meeting(filename, date.today(), transcript)
        result = run_extraction_review(meeting, transcript)
        return {"status": "awaiting_review", "filename": filename, **result}
    except Exception as error:
        raise _media_error(error) from error


@app.post("/review")
def review(req: ReviewRequest):
    """Legacy LangGraph bulk resume (prefer per-item review + dispatch)."""
    config = {"configurable": {"thread_id": req.thread_id}}
    result = graph.invoke(Command(resume=req.decision.model_dump()), config)
    return {"status": "completed", "thread_id": req.thread_id, "result": result}


@app.get("/meetings/{meeting_id}")
def get_meeting(meeting_id: str):
    """Meeting record, action items, and audit trail for demo / judges."""
    try:
        repository = InsForgeRepository()
        meeting = repository.get_one("meetings", meeting_id)
        if not meeting:
            raise LookupError("Meeting not found.")
        items = repository.list("action_items", {"meeting_id": f"eq.{meeting_id}"}, order="created_at.asc")
        audits = repository.list("audit_events", {"meeting_id": f"eq.{meeting_id}"}, order="created_at.asc")
        return {"meeting": meeting, "action_items": items, "audit_events": audits}
    except Exception as error:
        raise _media_error(error) from error


@app.post("/media/uploads")
def prepare_media_upload(req: MediaUploadRequest):
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


@app.post("/media/direct-upload")
async def direct_media_upload(file: UploadFile = File(...)):
    try:
        content = await file.read()
        filename = Path(file.filename or "recording.mp4").name
        content_type = file.content_type or "video/mp4"
        upload = create_upload(filename, date.today(), filename, content_type, len(content))
        store = GCSMediaStore()
        store.upload_bytes(upload["media"]["object_key"], content, content_type)
        confirm_upload(upload["media"]["id"])
        media, transcription = transcribe_media(upload["media"]["id"])
        review = _start_media_review(media, transcription.text)
        return {
            "media_id": upload["media"]["id"],
            "meeting_id": upload["meeting"]["id"],
            "status": "awaiting_review",
            "review": review,
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
    try:
        return {"results": dispatch_approved_candidates(InsForgeRepository(), meeting_id)}
    except Exception as error:
        raise _media_error(error) from error


@app.get("/health")
def health():
    return {"status": "ok", "dry_run": __import__("os").getenv("DRY_RUN", "true")}


@app.get("/upload-ui", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
def get_upload_ui():
    ui_path = Path("templates/ui.html")
    if not ui_path.exists():
        raise HTTPException(status_code=404, detail="UI template not found.")
    return HTMLResponse(content=ui_path.read_text(encoding="utf-8"))
