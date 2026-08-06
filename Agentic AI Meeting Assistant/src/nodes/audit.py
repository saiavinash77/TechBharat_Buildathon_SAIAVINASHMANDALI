from typing import List

try:
    from src.insforge_client import InsForgeRepository, InsForgeConfigurationError
except Exception:  # pragma: no cover - graceful fallback
    InsForgeRepository = None  # type: ignore
    InsForgeConfigurationError = Exception  # type: ignore


def audit_node(meeting_id: str, items: List[dict], hashes: List[str], results: List[dict]) -> None:
    """Record executed actions in InsForge audit_events. Never crashes the graph.

    If InsForge is not configured, a 1-line warning is printed and execution
    continues (no-op). This keeps local-demo behaviour working without any
    backend configured.
    """
    if InsForgeRepository is None:  # import guard
        print("[audit_node] InsForge not imported — skipping audit write (no-op fallback).")
        return
    try:
        repository = InsForgeRepository()
    except InsForgeConfigurationError:
        print("[audit_node] InsForge not configured — skipping audit write (no-op fallback).")
        return

    for item, h, res in zip(items, hashes, results):
        # A failed dispatch must remain retryable and therefore should not be
        # permanently logged as a successful audit event.
        if not (res.get("success") or res.get("dry_run")):
            continue
        event_type = "EXECUTE_DRY_RUN" if res.get("dry_run") else "EXECUTE_SUCCESS"
        try:
            repository.insert("audit_events", {
                "meeting_id": meeting_id,
                "action_item_id": None,
                "event_type": event_type,
                "actor_type": "SYSTEM",
                "payload": {
                    "action_hash": h,
                    "action_title": item.get("action_title", ""),
                    "github_result": res,
                },
            })
        except Exception as exc:  # Never let a single audit insert break the flow
            print(f"[audit_node] Failed to insert audit event for hash {h}: {exc}")
