"""Optional Slack recap after reviewer-approved dispatch."""

from __future__ import annotations

import os
from typing import Any

import requests


def post_meeting_recap(meeting: dict, dispatched: list[dict[str, Any]]) -> dict[str, Any]:
    """Post a recap to Slack when SLACK_WEBHOOK_URL is configured."""
    webhook = os.getenv("SLACK_WEBHOOK_URL", "").strip()
    if not webhook:
        return {"skipped": True, "reason": "SLACK_WEBHOOK_URL not configured"}

    if not dispatched:
        return {"skipped": True, "reason": "No dispatched items"}

    lines = [
        f"*Meeting recap:* {meeting.get('title', 'Untitled')}",
        f"*Date:* {meeting.get('meeting_date', '—')}",
        "",
        "*Approved action items:*",
    ]
    for item in dispatched:
        if item.get("status") == "already_dispatched":
            continue
        title = item.get("title") or item.get("action_item_id", "Item")
        url = item.get("html_url") or (item.get("result") or {}).get("issue_url")
        suffix = f" — <{url}|GitHub issue>" if url and not str(url).startswith("[DRY RUN]") else ""
        lines.append(f"• {title}{suffix}")

    payload = {"text": "\n".join(lines)}
    try:
        resp = requests.post(webhook, json=payload, timeout=10)
        if resp.status_code >= 400:
            return {"success": False, "status": resp.status_code, "detail": resp.text[:500]}
        return {"success": True}
    except requests.RequestException as error:
        return {"success": False, "error": str(error)}
