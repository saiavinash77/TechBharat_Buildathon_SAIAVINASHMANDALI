import hashlib
from typing import List

try:
    from src.insforge_client import InsForgeRepository, InsForgeConfigurationError
except Exception:  # pragma: no cover - graceful fallback
    InsForgeRepository = None  # type: ignore
    InsForgeConfigurationError = Exception  # type: ignore


def generate_action_hash(meeting_id: str, owner: str, title: str) -> str:
    raw = f"{meeting_id.strip().lower()}:{owner.strip().lower()}:{title.strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def dedup_node(meeting_id: str, approved_items: List[dict]) -> tuple[List[str], List[dict]]:
    """SHA256 idempotency check against InsForge dispatch_attempts. Returns (hashes, filtered_items).

    Falls back to NO dedup (passes all items through) if InsForge credentials are missing.
    This keeps local-dev behaviour working and never crashes the graph node.
    """
    if InsForgeRepository is None:  # graceful import guard
        hashes = [
            generate_action_hash(meeting_id, it.get("owner_name", ""), it.get("action_title", ""))
            for it in approved_items
        ]
        return hashes, list(approved_items)

    try:
        repository = InsForgeRepository()
    except InsForgeConfigurationError:
        print("[dedup_node] InsForge not configured — skipping dedup check (no-op fallback).")
        hashes = [
            generate_action_hash(meeting_id, it.get("owner_name", ""), it.get("action_title", ""))
            for it in approved_items
        ]
        return hashes, list(approved_items)

    hashes = []
    filtered = []

    for item in approved_items:
        if item.get("classification") not in {"EXPLICIT_COMMITMENT", "NEEDS_CONFIRMATION"}:
            continue
        if item.get("classification") == "EXPLICIT_COMMITMENT" and item.get("owner_explicitly_accepted") is not True:
            continue
        h = generate_action_hash(meeting_id, item.get("owner_name", ""), item.get("action_title", ""))
        try:
            exists = repository.find_one("dispatch_attempts", {"idempotency_key": f"eq.{h}"})
        except Exception:
            exists = None
        if exists:
            continue  # Skip duplicate
        hashes.append(h)
        filtered.append(item)

    return hashes, filtered
