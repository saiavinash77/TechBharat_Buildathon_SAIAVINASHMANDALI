import hashlib
from typing import List

from src.models import AuditLog
from src.utils.db import get_db


def generate_action_hash(meeting_id: str, owner: str, title: str) -> str:
    raw = f"{meeting_id.strip().lower()}:{owner.strip().lower()}:{title.strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def dedup_node(meeting_id: str, approved_items: List[dict]) -> tuple[List[str], List[dict]]:
    """Stage 6: SHA256 idempotency check. Returns (hashes, filtered_items)."""
    db = next(get_db())
    hashes = []
    filtered = []

    for item in approved_items:
        if item.get("classification") not in {"EXPLICIT_COMMITMENT", "NEEDS_CONFIRMATION"}:
            continue
        if item.get("classification") == "EXPLICIT_COMMITMENT" and item.get("owner_explicitly_accepted") is not True:
            continue
        h = generate_action_hash(meeting_id, item.get("owner_name", ""), item.get("action_title", ""))
        exists = db.query(AuditLog).filter(AuditLog.action_hash == h).first()
        if exists:
            continue  # Skip duplicate
        hashes.append(h)
        filtered.append(item)

    db.close()
    return hashes, filtered
