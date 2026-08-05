from datetime import datetime
from typing import List, Dict, Any

from src.models import AuditLog
from src.utils.db import get_db


def audit_node(meeting_id: str, items: List[dict], hashes: List[str], results: List[dict]) -> None:
    """Stage 8: Record every executed action in audit trail."""
    db = next(get_db())
    for item, h, res in zip(items, hashes, results):
        # A failed dispatch must remain retryable and therefore cannot reserve
        # the idempotency key as a completed action.
        if not res.get("success"):
            continue
        log = AuditLog(
            meeting_id=meeting_id,
            action_hash=h,
            action_title=item.get("action_title", ""),
            owner_name=item.get("owner_name", ""),
            target_tool="GitHub Issues",
            approved_by="Human Reviewer",
            payload={"github_result": res},
        )
        db.add(log)
    db.commit()
    db.close()
