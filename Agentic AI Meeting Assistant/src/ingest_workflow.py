"""Unified transcript ingestion: extract, persist candidates, return review payload."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

from src.durable_workflow import persist_candidates
from src.graph import graph
from src.insforge_client import InsForgeRepository
from src.state import AgentState


def create_text_meeting(title: str, meeting_date: date, transcript: str) -> dict:
    repository = InsForgeRepository()
    meeting_key = f"mtg_{uuid4().hex[:12]}"
    meeting = repository.insert("meetings", {
        "meeting_key": meeting_key,
        "title": title.strip() or "Text transcript meeting",
        "meeting_date": meeting_date.isoformat(),
        "transcript_text": transcript,
        "transcript_hash": "0" * 64,
        "processing_status": "EXTRACTING",
    })
    return meeting


def run_extraction_review(meeting: dict, transcript: str) -> dict:
    """Run LangGraph through review interrupt and persist durable candidates."""
    repository = InsForgeRepository()
    meeting_id = meeting["id"]
    thread_id = f"meeting-{meeting_id}"
    config = {"configurable": {"thread_id": thread_id}}

    state: AgentState = {
        "transcript": transcript,
        "meeting_date": str(meeting["meeting_date"]),
        "meeting_id": meeting["meeting_key"],
        "approved_items": [],
        "rejected_items": [],
        "action_hashes": [],
        "execution_results": [],
    }
    graph.invoke(state, config)
    snapshot = graph.get_state(config)

    if not snapshot:
        raise RuntimeError("Extraction pipeline failed to produce state.")

    extracted = snapshot.values.get("extracted")
    if extracted is not None and getattr(extracted, "executive_summary", "").startswith("Extraction failed"):
        raise RuntimeError(extracted.executive_summary)

    if not (snapshot.tasks and snapshot.tasks[0].interrupts):
        raise RuntimeError("Extraction did not produce reviewable candidates.")

    candidates = persist_candidates(
        repository,
        meeting_id,
        thread_id,
        extracted.action_items if extracted else [],
    )
    repository.update("meetings", meeting_id, {
        "processing_status": "AWAITING_REVIEW",
        "transcript_text": transcript,
    })

    payload = dict(snapshot.tasks[0].interrupts[0].value)
    payload["items"] = candidates
    if extracted:
        payload["decisions"] = extracted.decisions_made
        payload["open_questions"] = extracted.open_questions
        payload["risks_or_blockers"] = getattr(extracted, "risks_or_blockers", [])

    return {
        "meeting_id": meeting_id,
        "meeting_key": meeting["meeting_key"],
        "thread_id": thread_id,
        "status": "awaiting_review",
        "review": {"thread_id": thread_id, "payload": payload},
    }
