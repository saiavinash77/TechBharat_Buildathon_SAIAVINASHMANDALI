import os
from datetime import date, datetime, timezone
from pathlib import Path
import uuid
import json

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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
    error_message = str(error) or "Media processing failed. Check server logs for the provider error."
    return HTTPException(status_code=502, detail=error_message)


def _build_empty_transcript_review_payload(meeting_id: str, transcript: str) -> dict:
    """Create a user-friendly review payload when the source media was empty or unintelligible."""
    normalized = (transcript or "").strip()
    if not normalized:
        summary = "No speech was detected in the uploaded audio. Please upload a clearer recording or use the text transcript option."
        reason = "empty_transcript"
    elif len(normalized) < 30:
        summary = "The transcript was too short to derive reliable action items. Please upload a clearer recording or paste a transcript manually."
        reason = "short_transcript"
    else:
        summary = "No reviewable action items were detected from this transcript."
        reason = "no_candidates"

    return {
        "type": "review_required",
        "meeting_id": meeting_id,
        "summary": summary,
        "items": [],
        "rules": {
            "explicit_commitment": "May be assigned only when the speaker directly accepted it.",
            "needs_confirmation": "May be sent to GitHub unassigned with needs-confirmation.",
            "discussion_only": "Must not be sent to GitHub.",
        },
        "empty_reason": reason,
    }


def _start_media_review(media: dict, transcript: str) -> dict | None:
    """Immediately hand a completed transcript to the LangGraph review gate."""
    repository = InsForgeRepository()
    meeting = repository.get_one("meetings", media["meeting_id"])
    if not meeting:
        raise LookupError("Meeting metadata not found for this media file.")
    normalized = (transcript or "").strip()
    if not normalized or len(normalized) < 30:
        return {"thread_id": f"meeting-{meeting['id']}", "payload": _build_empty_transcript_review_payload(meeting["meeting_key"], transcript)}

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


def _local_data_path(table: str) -> Path:
    base = Path(__file__).resolve().parents[1] / "files"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{table}.json"


class LocalRepository:
    """Simple file-backed repository implementing a small subset of InsForgeRepository methods used by the workflow.

    This is intended only for local testing/demo when USE_INSFORGE is not enabled.
    """

    def __init__(self):
        pass

    def _read(self, table: str) -> list:
        path = _local_data_path(table)
        try:
            data = json.loads(path.read_text()) if path.exists() else []
            if isinstance(data, list):
                return data
            if data is None:
                return []
            # If file contains a single object, wrap it into a list
            return [data]
        except Exception:
            return []

    def _write(self, table: str, rows: list):
        path = _local_data_path(table)
        path.write_text(json.dumps(rows))
        return rows

    def insert(self, table: str, record: dict) -> dict:
        rows = self._read(table)
        # ensure id
        if "id" not in record:
            record = {**record, "id": uuid.uuid4().hex}
        rows.append(record)
        self._write(table, rows)
        return record

    def get_one(self, table: str, record_id: str) -> dict | None:
        rows = self._read(table)
        for r in rows:
            if str(r.get("id")) == str(record_id):
                return r
        return None

    def find_one(self, table: str, filters: dict) -> dict | None:
        rows = self._read(table)
        for r in rows:
            ok = True
            for k, v in (filters or {}).items():
                if isinstance(v, str) and v.startswith("eq."):
                    if str(r.get(k)) != v[3:]:
                        ok = False
                        break
                else:
                    if r.get(k) != v:
                        ok = False
                        break
            if ok:
                return r
        return None

    def list(self, table: str, filters: dict | None = None, *, order: str | None = None) -> list:
        rows = self._read(table)
        if filters:
            def matches(r):
                for k, v in filters.items():
                    if isinstance(v, str) and v.startswith("eq."):
                        if str(r.get(k)) != v[3:]:
                            return False
                    else:
                        if r.get(k) != v:
                            return False
                return True
            rows = [r for r in rows if matches(r)]
        if order:
            # very small support for 'created_at.asc'
            parts = order.split(".")
            key = parts[0]
            reverse = parts[-1] != "asc"
            rows = sorted(rows, key=lambda x: x.get(key) or "", reverse=reverse)
        return rows

    def update(self, table: str, record_id: str, changes: dict) -> dict:
        rows = self._read(table)
        updated = None
        for i, r in enumerate(rows):
            if str(r.get("id")) == str(record_id):
                rows[i] = {**r, **changes}
                updated = rows[i]
                break
        if updated is None:
            raise LookupError(f"Record {record_id} not found in {table}")
        self._write(table, rows)
        return updated


def _get_repository():
    use_insforge = os.getenv("USE_INSFORGE", "").lower() in ("1", "true", "yes")
    if use_insforge:
        return InsForgeRepository()
    return LocalRepository()


@app.post("/meetings/{meeting_id}/dispatch")
def dispatch_meeting_candidates(meeting_id: str):
    """Create only reviewer-approved eligible GitHub issues; dry run is the default."""
    try:
        repo = _get_repository()
        return {"results": dispatch_approved_candidates(repo, meeting_id)}
    except Exception as error:
        raise _media_error(error) from error


@app.get("/meetings/{meeting_id}/action-items")
def list_meeting_action_items(meeting_id: str):
    """Return stored action items for a meeting (used by the UI)."""
    try:
        repo = _get_repository()
        items = repo.list("action_items", {"meeting_id": f"eq.{meeting_id}"})
        return {"meeting_id": meeting_id, "items": items}
    except Exception as error:
        raise _media_error(error) from error


class InviteRequest(BaseModel):
    org_id: str
    inviter_name: str | None = None


class JoinRequest(BaseModel):
    token: str
    name: str
    email: str
    github_handle: str | None = None


def _local_store_path(name: str) -> Path:
    base = Path(__file__).resolve().parents[1] / "files"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{name}.json"


@app.post("/invites")
def create_invite(req: InviteRequest):
    """Create a multi-use invite token for an organization.

    Tries InsForgeRepository first; if that fails (missing table or config), falls back to a local JSON store in files/org_invites.json.
    """
    token = uuid.uuid4().hex[:22]
    invite_record = {
        "org_id": req.org_id,
        "token": token,
        "inviter_name": req.inviter_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    # Only attempt InsForge when explicitly enabled; default to local storage to avoid remote failures
    use_insforge = os.getenv("USE_INSFORGE", "").lower() in ("1", "true", "yes")
    if use_insforge:
        try:
            repo = InsForgeRepository()
            invite = repo.insert("org_invites", invite_record)
            join_url = f"/join?token={token}"
            return {"invite": invite, "join_url": join_url}
        except Exception:
            # fall through to local fallback
            pass
    # Fallback: persist locally
    path = _local_store_path("org_invites")
    try:
        current = json.loads(path.read_text()) if path.exists() else []
    except Exception:
        current = []
    current.append(invite_record)
    path.write_text(json.dumps(current))
    return {"invite": invite_record, "join_url": f"/join?token={token}", "note": "stored-locally"}


@app.get("/join")
def get_join(token: str):
    """Fetch invite details by token so the UI can render a join form.

    Tries InsForgeRepository first; if that fails, looks up the token in local files/org_invites.json.
    """
    # Only attempt InsForge when explicitly enabled; default to local lookup to avoid remote failures
    use_insforge = os.getenv("USE_INSFORGE", "").lower() in ("1", "true", "yes")
    if use_insforge:
        try:
            repo = InsForgeRepository()
            invite = repo.find_one("org_invites", {"token": f"eq.{token}"})
            if invite:
                return {"token": invite["token"], "org_id": invite["org_id"], "inviter_name": invite.get("inviter_name"), "created_at": invite.get("created_at")}
        except Exception:
            pass
    path = _local_store_path("org_invites")
    try:
        current = json.loads(path.read_text()) if path.exists() else []
    except Exception:
        current = []
    for inv in current:
        if inv.get("token") == token:
            return {"token": inv["token"], "org_id": inv["org_id"], "inviter_name": inv.get("inviter_name"), "created_at": inv.get("created_at")}
    raise HTTPException(status_code=404, detail="Invite token not found")


@app.post("/join")
def post_join(req: JoinRequest):
    """Complete a join: upsert user by email and add to the organization members table.

    Tries InsForgeRepository first; if that fails, performs a local JSON upsert in files/users.json and files/organization_members.json.
    """
    # Only attempt InsForge when explicitly enabled; default to local paths to avoid remote failures
    use_insforge = os.getenv("USE_INSFORGE", "").lower() in ("1", "true", "yes")
    if use_insforge:
        try:
            repo = InsForgeRepository()
            invite = repo.find_one("org_invites", {"token": f"eq.{req.token}"})
            if not invite:
                raise LookupError("Invite token not found")
            # Upsert user by email
            user = repo.find_one("users", {"email": f"eq.{req.email}"})
            if user:
                user = repo.update("users", user["id"], {"name": req.name, "github_handle": req.github_handle})
            else:
                user = repo.insert("users", {"name": req.name, "email": req.email, "github_handle": req.github_handle})
            # Ensure organization membership
            membership = repo.find_one("organization_members", {"org_id": f"eq.{invite['org_id']}", "user_id": f"eq.{user['id']}"})
            if not membership:
                repo.insert("organization_members", {"org_id": invite["org_id"], "user_id": user["id"], "joined_at": datetime.now(timezone.utc).isoformat()})
            return {"status": "joined", "org_id": invite["org_id"], "user": user}
        except Exception:
            # fall through to local fallback
            pass
    # Fallback local upsert
    # find invite locally
    path = _local_store_path("org_invites")
    try:
        current = json.loads(path.read_text()) if path.exists() else []
    except Exception:
        current = []
    invite = next((i for i in current if i.get("token") == req.token), None)
    if not invite:
        raise HTTPException(status_code=404, detail="Invite token not found")
    # upsert user
    users_path = _local_store_path("users")
    try:
        users = json.loads(users_path.read_text()) if users_path.exists() else []
    except Exception:
        users = []
    user = next((u for u in users if u.get("email") == req.email), None)
    if user:
        user["name"] = req.name
        user["github_handle"] = req.github_handle
    else:
        user = {"id": uuid.uuid4().hex, "name": req.name, "email": req.email, "github_handle": req.github_handle}
        users.append(user)
    users_path.write_text(json.dumps(users))
    # ensure membership
    members_path = _local_store_path("organization_members")
    try:
        members = json.loads(members_path.read_text()) if members_path.exists() else []
    except Exception:
        members = []
    if not any(m for m in members if m.get("org_id") == invite["org_id"] and m.get("user_id") == user["id"]):
        members.append({"org_id": invite["org_id"], "user_id": user["id"], "joined_at": datetime.now(timezone.utc).isoformat()})
        members_path.write_text(json.dumps(members))
    # Also map the provided GitHub handle to any existing action items whose owner matches this user's name or email
    try:
        ai_path = _local_store_path("action_items")
        action_items = json.loads(ai_path.read_text()) if ai_path.exists() else []
    except Exception:
        action_items = []
    updated = False
    for it in action_items:
        if not it.get("github_assignee_login") and user.get("github_handle"):
            owner_names = [it.get("final_owner_name"), it.get("owner_name"), it.get("owner"), it.get("assigned_to")]
            if any(owner and owner == user.get("name") or owner == user.get("email") for owner in owner_names if owner):
                it["github_assignee_login"] = user.get("github_handle")
                updated = True
    if updated:
        try:
            ai_path.write_text(json.dumps(action_items))
        except Exception:
            pass
    return {"status": "joined", "org_id": invite["org_id"], "user": user, "note": "stored-locally"}


@app.get("/orgs/{org_id}/members")
def list_org_members(org_id: str):
    """Return a list of members for an organization.

    By default uses local files; set USE_INSFORGE=1 to fetch from InsForge.
    """
    use_insforge = os.getenv("USE_INSFORGE", "").lower() in ("1", "true", "yes")
    if use_insforge:
        try:
            repo = InsForgeRepository()
            members = repo.query("organization_members", {"org_id": f"eq.{org_id}"})
            # members likely include user_id; fetch user records
            results = []
            for m in members:
                user = repo.find_one("users", {"id": f"eq.{m['user_id']}"})
                if user:
                    results.append({"user": user, "joined_at": m.get("joined_at")})
            return {"org_id": org_id, "members": results}
        except Exception:
            pass
    # Local fallback
    members_path = _local_store_path("organization_members")
    users_path = _local_store_path("users")
    try:
        members = json.loads(members_path.read_text()) if members_path.exists() else []
    except Exception:
        members = []
    try:
        users = json.loads(users_path.read_text()) if users_path.exists() else []
    except Exception:
        users = []
    results = []
    for m in members:
        if m.get("org_id") == org_id:
            user = next((u for u in users if u.get("id") == m.get("user_id")), None)
            results.append({"user": user, "joined_at": m.get("joined_at")})
    return {"org_id": org_id, "members": results}


@app.get("/health")
def health():
    return {"status": "ok"}


def _is_placeholder_github_token(token: str | None) -> bool:
    normalized = (token or "").strip()
    return normalized == "" or normalized in {"******", "your-token-here", "<token>"}


@app.get("/config")
def get_config():
    """Return a small public configuration payload for the UI to validate uploads."""
    try:
        max_bytes = int(os.getenv("MEDIA_MAX_UPLOAD_BYTES", "524288000"))
    except ValueError:
        max_bytes = 524288000
    dry = os.getenv("DRY_RUN", "").lower() in ("1", "true", "yes")
    project = os.getenv("GCP_PROJECT_ID") or None
    github_repo = os.getenv("GITHUB_REPO")
    github_token = os.getenv("GITHUB_TOKEN")
    github_enabled = bool(github_repo and not _is_placeholder_github_token(github_token))
    return {
        "media_max_upload_bytes": max_bytes,
        "dry_run": dry,
        "gcp_project_id": project,
        "github_repo": github_repo,
        "github_enabled": github_enabled,
    }


@app.get("/", response_class=HTMLResponse)
@app.get("/upload-ui", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
def get_upload_ui():
    ui_path = Path("templates/ui.html")
    if not ui_path.exists():
        raise HTTPException(status_code=404, detail="UI template not found.")
    return HTMLResponse(content=ui_path.read_text(encoding="utf-8"))


@app.get('/join-ui', response_class=HTMLResponse)
def get_join_ui():
    join_path = Path('templates/join.html')
    if not join_path.exists():
        raise HTTPException(status_code=404, detail='Join UI template not found.')
    return HTMLResponse(content=join_path.read_text(encoding='utf-8'))
