"""InsForge-backed candidate review and GitHub dispatch operations."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

from src.insforge_client import InsForgeRepository
from src.nodes.execute import execute_node
from src.slack_recap import post_meeting_recap
from src.state import ActionItem


ELIGIBLE_CLASSIFICATIONS = {"EXPLICIT_COMMITMENT", "NEEDS_CONFIRMATION"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _candidate_payload(item: ActionItem) -> dict[str, Any]:
    snapshot = item.model_dump(mode="json")
    return {
        "original_title": item.action_title,
        "final_title": item.action_title,
        "speaker_name": item.speaker_name,
        "quote_provenance": item.quote_provenance,
        "classification": item.classification,
        "proposed_owner_name": None if item.owner_name == "Unassigned" else item.owner_name,
        "owner_explicitly_accepted": item.owner_explicitly_accepted,
        "raw_due_date_mention": item.raw_due_date_mention or None,
        "resolved_due_date": item.resolved_due_date,
        "priority": item.priority,
        "confidence_score": item.confidence_score,
        "extraction_reason": item.extraction_reason,
        "original_snapshot": snapshot,
        "review_status": "PENDING_REVIEW",
        "dispatch_status": "NOT_READY",
    }


def _review_view(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item["id"],
        "title": item["final_title"],
        "speaker_name": item["speaker_name"],
        "classification": item["classification"],
        "proposed_owner_name": item.get("proposed_owner_name"),
        "final_owner_name": item.get("final_owner_name"),
        "owner_explicitly_accepted": item["owner_explicitly_accepted"],
        "due_date": item.get("resolved_due_date"),
        "priority": item["priority"],
        "confidence_score": item["confidence_score"],
        "quote_provenance": item["quote_provenance"],
        "extraction_reason": item["extraction_reason"],
        "review_status": item["review_status"],
        "reviewed_by": item.get("reviewed_by"),
        "github_assignee_login": item.get("github_assignee_login"),
        "dispatch_status": item.get("dispatch_status"),
    }


def persist_candidates(repository: InsForgeRepository, meeting_id: str, thread_id: str, candidates: list[ActionItem]) -> list[dict[str, Any]]:
    """Save one immutable AI proposal per candidate before a reviewer can act."""
    existing = repository.list("action_items", {"meeting_id": f"eq.{meeting_id}"}, order="created_at.asc")
    if existing:
        return [_review_view(item) for item in existing]

    stored = []
    for candidate in candidates:
        stored.append(repository.insert("action_items", {"meeting_id": meeting_id, **_candidate_payload(candidate)}))

    run = repository.find_one("workflow_runs", {"meeting_id": f"eq.{meeting_id}"})
    checkpoint = {"thread_id": thread_id, "candidate_count": len(stored), "status": "AWAITING_REVIEW"}
    if run:
        repository.update("workflow_runs", run["id"], {"status": "AWAITING_REVIEW", "checkpoint_payload": checkpoint})
    else:
        repository.insert("workflow_runs", {
            "meeting_id": meeting_id,
            "thread_id": thread_id,
            "status": "AWAITING_REVIEW",
            "checkpoint_payload": checkpoint,
        })
    repository.insert("audit_events", {
        "meeting_id": meeting_id,
        "event_type": "EXTRACTION_COMPLETED",
        "actor_type": "SYSTEM",
        "payload": {"candidate_count": len(stored), "thread_id": thread_id},
    })
    return [_review_view(item) for item in stored]


def review_candidate(
    repository: InsForgeRepository,
    meeting_id: str,
    action_item_id: str,
    *,
    reviewer_name: str,
    decision: str,
    note: str = "",
    final_title: str | None = None,
    priority: str | None = None,
    resolved_due_date: str | None = None,
    github_assignee_login: str | None = None,
    final_owner_name: str | None = None,
) -> dict[str, Any]:
    item = repository.get_one("action_items", action_item_id)
    if not item or item["meeting_id"] != meeting_id:
        raise LookupError("Action item not found in this meeting.")
    if decision not in {"APPROVED", "EDITED", "REJECTED", "REEXTRACTION_REQUESTED"}:
        raise ValueError("Invalid review decision.")

    if decision == "APPROVED" and item["classification"] not in ELIGIBLE_CLASSIFICATIONS:
        raise ValueError("Discussion-only items cannot be approved for GitHub dispatch.")
    if github_assignee_login and not (
        item["classification"] == "EXPLICIT_COMMITMENT" and item["owner_explicitly_accepted"] is True
    ):
        raise ValueError("Only an explicit self-commitment may receive a GitHub assignee.")

    changes: dict[str, Any] = {}
    if final_title:
        changes["final_title"] = final_title.strip()
    if priority:
        if priority not in {"HIGH", "MEDIUM", "LOW"}:
            raise ValueError("Priority must be HIGH, MEDIUM, or LOW.")
        changes["priority"] = priority
    if resolved_due_date:
        changes["resolved_due_date"] = resolved_due_date
    if github_assignee_login:
        changes["github_assignee_login"] = github_assignee_login
    if final_owner_name:
        changes["final_owner_name"] = final_owner_name.strip()

    if decision == "APPROVED":
        changes.update({"review_status": "APPROVED", "dispatch_status": "PENDING", "reviewed_by": reviewer_name, "reviewed_at": _now()})
    elif decision == "REJECTED":
        changes.update({"review_status": "REJECTED", "dispatch_status": "NOT_ELIGIBLE", "reviewed_by": reviewer_name, "reviewed_at": _now()})
    elif decision == "REEXTRACTION_REQUESTED":
        changes.update({"review_status": "REEXTRACTION_REQUESTED", "dispatch_status": "NOT_READY", "reviewed_by": reviewer_name, "reviewed_at": _now()})
    elif decision == "EDITED":
        changes.update({
            "review_status": "PENDING_REVIEW",
            "dispatch_status": "NOT_READY",
            "reviewed_by": reviewer_name,
            "reviewed_at": _now(),
        })

    updated = repository.update("action_items", action_item_id, changes) if changes else item
    repository.insert("action_item_reviews", {
        "action_item_id": action_item_id,
        "reviewer_name": reviewer_name,
        "decision": decision,
        "reviewer_note": note,
        "original_snapshot": item["original_snapshot"],
        "final_snapshot": updated,
    })
    repository.insert("audit_events", {
        "meeting_id": meeting_id,
        "action_item_id": action_item_id,
        "event_type": f"REVIEW_{decision}",
        "actor_type": "REVIEWER",
        "actor_name": reviewer_name,
        "payload": {"note": note},
    })
    return _review_view(updated)


def _idempotency_key(meeting_id: str, item: dict[str, Any]) -> str:
    raw = f"{meeting_id}:{item['id']}:{item['final_title']}:{item.get('github_assignee_login') or ''}"
    return sha256(raw.encode("utf-8")).hexdigest()


def dispatch_approved_candidates(repository: InsForgeRepository, meeting_id: str) -> list[dict[str, Any]]:
    """Dispatch only stored, reviewer-approved candidates; keep failures retryable."""
    results = []
    items = repository.list("action_items", {"meeting_id": f"eq.{meeting_id}"})
    for item in items:
        if item["review_status"] != "APPROVED" or item["dispatch_status"] not in {"PENDING", "FAILED"}:
            continue
        key = _idempotency_key(meeting_id, item)
        attempt = repository.find_one("dispatch_attempts", {"action_item_id": f"eq.{item['id']}"})
        if attempt and attempt["status"] == "DISPATCHED":
            results.append({"action_item_id": item["id"], "status": "already_dispatched"})
            continue
        if attempt:
            attempt = repository.update("dispatch_attempts", attempt["id"], {
                "status": "PROCESSING", "attempt_count": attempt["attempt_count"] + 1, "last_error": None,
            })
        else:
            attempt = repository.insert("dispatch_attempts", {
                "action_item_id": item["id"], "idempotency_key": key, "status": "PROCESSING", "attempt_count": 1,
                "request_payload": {"title": item["final_title"], "classification": item["classification"]},
            })

        payload = {
            "action_title": item["final_title"], "classification": item["classification"],
            "owner_explicitly_accepted": item["owner_explicitly_accepted"],
            "owner_name": item.get("final_owner_name") or item.get("proposed_owner_name") or "Unassigned",
            "speaker_name": item["speaker_name"], "github_assignee_login": item.get("github_assignee_login"),
            "resolved_due_date": item.get("resolved_due_date"), "priority": item["priority"],
            "quote_provenance": item["quote_provenance"],
        }
        result = execute_node(meeting_id, [payload], [key])[0]
        if result.get("dry_run"):
            repository.update("dispatch_attempts", attempt["id"], {"status": "PENDING", "response_payload": result})
            event_type, dispatch_status = "DISPATCH_PREVIEWED", "PENDING"
        elif result.get("success"):
            repository.update("dispatch_attempts", attempt["id"], {"status": "DISPATCHED", "response_payload": result, "github_issue_url": result.get("issue_url")})
            event_type, dispatch_status = "GITHUB_ISSUE_DISPATCHED", "DISPATCHED"
        else:
            detail = result.get("detail") or result.get("error") or result.get("reason") or "Unknown dispatch failure"
            repository.update("dispatch_attempts", attempt["id"], {"status": "FAILED", "response_payload": result, "last_error": detail})
            event_type, dispatch_status = "GITHUB_DISPATCH_FAILED", "FAILED"
        repository.update("action_items", item["id"], {"dispatch_status": dispatch_status})
        repository.insert("audit_events", {
            "meeting_id": meeting_id, "action_item_id": item["id"], "event_type": event_type,
            "actor_type": "SYSTEM", "payload": result,
        })
        results.append({
            "action_item_id": item["id"],
            "title": item["final_title"],
            "status": dispatch_status.lower(),
            "html_url": result.get("issue_url"),
            "dry_run": result.get("dry_run", False),
            "result": result,
        })

    if results:
        meeting = repository.get_one("meetings", meeting_id)
        slack_result = post_meeting_recap(meeting or {}, results)
        if not slack_result.get("skipped"):
            repository.insert("audit_events", {
                "meeting_id": meeting_id,
                "event_type": "SLACK_RECAP_POSTED" if slack_result.get("success") else "SLACK_RECAP_FAILED",
                "actor_type": "SYSTEM",
                "payload": slack_result,
            })

    return results
