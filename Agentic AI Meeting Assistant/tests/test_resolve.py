from src.nodes.resolve import resolve_node
from src.state import ActionItem, MeetingRecord


def test_resolve_normalizes_an_explicit_owner_date_and_confidence():
    record = MeetingRecord(
        action_items=[
            ActionItem(
                    action_title="Complete the database migration",
                    owner_name="Rahul",
                    speaker_name="Rahul",
                    classification="EXPLICIT_COMMITMENT",
                    owner_explicitly_accepted=True,
                    raw_due_date_mention="tomorrow",
                priority="HIGH",
                quote_provenance="Rahul: I will complete the database migration tomorrow.",
            )
        ]
    )

    resolved = resolve_node(
        record,
        "2026-08-05",
        roster={"Rahul Mehta": {"email": "rahul@example.com", "github": "rahul-dev", "aliases": ["rahul", "rahul mehta"]}},
    )
    item = resolved.action_items[0]

    assert item.owner_name == "Rahul Mehta"
    assert item.resolved_due_date == "2026-08-06"
    assert item.confidence_score == 1.0


def test_resolve_leaves_an_unknown_owner_visible_for_review():
    record = MeetingRecord(
        action_items=[
            ActionItem(
                action_title="Clarify the launch checklist",
                owner_name="Unassigned",
                raw_due_date_mention="",
                quote_provenance="We should clarify the launch checklist.",
            )
        ]
    )

    item = resolve_node(record, "2026-08-05", roster={}).action_items[0]

    assert item.owner_name == "Unassigned"
    assert item.resolved_due_date is None
    assert item.confidence_score == 0.5
