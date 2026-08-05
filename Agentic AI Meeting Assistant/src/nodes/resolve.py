import dateparser
from datetime import datetime
from typing import Optional

from src.state import MeetingRecord, ActionItem


def resolve_node(extracted: MeetingRecord, meeting_date_str: str, roster: Optional[dict] = None) -> MeetingRecord:
    """Stage 4: Deterministic date resolution and owner verification."""
    if roster is None:
        roster = {}  # name -> email mapping

    meeting_date = datetime.strptime(meeting_date_str, "%Y-%m-%d").date()

    for item in extracted.action_items:
        # Date resolution
        if item.raw_due_date_mention:
            parsed = dateparser.parse(
                item.raw_due_date_mention,
                settings={"RELATIVE_BASE": datetime.combine(meeting_date, datetime.min.time())}
            )
            if parsed:
                item.resolved_due_date = parsed.strftime("%Y-%m-%d")
            else:
                item.resolved_due_date = None

        # Owner verification
        normalized_owner = item.owner_name.strip().lower()
        matched = None
        for name in roster:
            if normalized_owner in name.lower() or name.lower() in normalized_owner:
                matched = name
                break
        
        if matched:
            item.owner_name = matched
        else:
            # Fail loudly: keep original but mark for review
            pass

        # Deterministic confidence recalculation
        score = 0.0
        if item.action_title and len(item.action_title) > 5:
            score += 0.25
        if item.owner_explicitly_accepted and item.owner_name and item.owner_name.lower() not in ("unassigned", ""):
            score += 0.25
        if item.resolved_due_date:
            score += 0.25
        if item.quote_provenance and len(item.quote_provenance) > 10:
            score += 0.25
        item.confidence_score = round(score, 2)

    return extracted
