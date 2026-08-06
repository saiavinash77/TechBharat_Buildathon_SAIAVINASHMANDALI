import dateparser
from datetime import datetime
from typing import Optional

from src.roster import load_roster, resolve_owner
from src.state import MeetingRecord


def resolve_node(extracted: MeetingRecord, meeting_date_str: str, roster: Optional[dict] = None) -> MeetingRecord:
    """Deterministic date resolution and roster-based owner verification."""
    roster_data = load_roster() if roster is None else roster
    meeting_date = datetime.strptime(meeting_date_str, "%Y-%m-%d").date()

    for item in extracted.action_items:
        if item.raw_due_date_mention:
            parsed = dateparser.parse(
                item.raw_due_date_mention,
                settings={"RELATIVE_BASE": datetime.combine(meeting_date, datetime.min.time())},
            )
            item.resolved_due_date = parsed.strftime("%Y-%m-%d") if parsed else None

        resolution = resolve_owner(item.owner_name, roster_data)
        item.owner_name = resolution["owner_name"]
        item.owner_resolution_status = resolution["owner_resolution_status"]
        item.suggested_github_login = resolution["github_login"]
        if resolution["owner_resolution_status"] == "UNRESOLVED" and item.owner_explicitly_accepted:
            item.extraction_reason = (
                (item.extraction_reason + " ").strip()
                + "WARNING: Owner could not be mapped to team roster — reviewer must verify."
            ).strip()

        score = 0.0
        if item.action_title and len(item.action_title) > 5:
            score += 0.25
        if item.owner_explicitly_accepted and item.owner_name.lower() not in ("unassigned", ""):
            score += 0.25
        if item.resolved_due_date:
            score += 0.25
        if item.quote_provenance and len(item.quote_provenance) > 10:
            score += 0.25
        item.confidence_score = round(score, 2)

    return extracted
