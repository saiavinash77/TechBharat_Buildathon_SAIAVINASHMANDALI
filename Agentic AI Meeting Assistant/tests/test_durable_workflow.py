import pytest

from src.durable_workflow import persist_candidates, review_candidate
from src.state import ActionItem


class FakeRepository:
    def __init__(self):
        self.tables = {name: [] for name in ("action_items", "workflow_runs", "audit_events", "action_item_reviews")}
        self.sequence = 0

    def list(self, table, filters=None, order=None):
        rows = list(self.tables[table])
        if filters and "meeting_id" in filters:
            meeting_id = filters["meeting_id"].removeprefix("eq.")
            rows = [row for row in rows if row.get("meeting_id") == meeting_id]
        return rows

    def find_one(self, table, filters):
        for row in self.tables[table]:
            if all(row.get(key) == value.removeprefix("eq.") for key, value in filters.items()):
                return row
        return None

    def get_one(self, table, record_id):
        return next((row for row in self.tables[table] if row["id"] == record_id), None)

    def insert(self, table, record):
        self.sequence += 1
        row = {"id": f"{table}-{self.sequence}", **record}
        self.tables[table].append(row)
        return row

    def update(self, table, record_id, changes):
        row = self.get_one(table, record_id)
        row.update(changes)
        return row


def explicit_candidate():
    return ActionItem(
        action_title="Publish the demo",
        owner_name="Asha",
        speaker_name="Asha",
        classification="EXPLICIT_COMMITMENT",
        owner_explicitly_accepted=True,
        quote_provenance="Asha: I will publish the demo by Friday.",
        priority="HIGH",
        confidence_score=1.0,
    )


def test_candidates_are_persisted_before_review():
    repository = FakeRepository()

    saved = persist_candidates(repository, "meeting-1", "thread-1", [explicit_candidate()])

    assert saved[0]["classification"] == "EXPLICIT_COMMITMENT"
    assert repository.tables["workflow_runs"][0]["status"] == "AWAITING_REVIEW"
    assert repository.tables["audit_events"][0]["event_type"] == "EXTRACTION_COMPLETED"


def test_needs_confirmation_cannot_receive_an_assignee():
    repository = FakeRepository()
    item = repository.insert("action_items", {
        "meeting_id": "meeting-1", "classification": "NEEDS_CONFIRMATION",
        "owner_explicitly_accepted": False, "original_snapshot": {}, "final_title": "Review proposal",
        "speaker_name": "Ravi", "priority": "MEDIUM", "confidence_score": 0.5,
        "quote_provenance": "Can Asha review the proposal?", "extraction_reason": "Request", "review_status": "PENDING_REVIEW",
    })

    with pytest.raises(ValueError, match="explicit self-commitment"):
        review_candidate(
            repository, "meeting-1", item["id"], reviewer_name="Reviewer", decision="APPROVED", github_assignee_login="asha"
        )


def test_approved_explicit_commitment_can_store_a_verified_login():
    repository = FakeRepository()
    stored = persist_candidates(repository, "meeting-1", "thread-1", [explicit_candidate()])[0]

    reviewed = review_candidate(
        repository, "meeting-1", stored["id"], reviewer_name="Reviewer", decision="APPROVED", github_assignee_login="asha"
    )

    assert reviewed["review_status"] == "APPROVED"
    assert repository.tables["action_item_reviews"][0]["decision"] == "APPROVED"


def test_edited_decision_updates_fields_and_leaves_item_reviewable():
    """An EDIT does NOT lock the item; it must remain re-reviewable in PENDING_REVIEW
    state, and edits like final_owner_name must actually persist."""
    repository = FakeRepository()
    stored = persist_candidates(repository, "meeting-1", "thread-1", [explicit_candidate()])[0]

    edited = review_candidate(
        repository, "meeting-1", stored["id"],
        reviewer_name="Editor", decision="EDITED",
        final_title="Publish the demo BEFORE Friday",
        final_owner_name="Asha Sharma",
        priority="MEDIUM",
        note="Changed due date and owner to match meeting consensus.",
    )

    assert edited["title"] == "Publish the demo BEFORE Friday"
    assert edited["priority"] == "MEDIUM"
    assert edited["final_owner_name"] == "Asha Sharma"
    assert edited["review_status"] == "PENDING_REVIEW"  # still re-reviewable, not bricked
    assert edited["reviewed_by"] == "Editor"

    raw_row = repository.get_one("action_items", stored["id"])
    assert raw_row["final_title"] == "Publish the demo BEFORE Friday"
    assert raw_row["final_owner_name"] == "Asha Sharma"
    assert raw_row["reviewed_by"] == "Editor"

    review_row = repository.tables["action_item_reviews"][-1]
    assert review_row["decision"] == "EDITED"
    assert review_row["reviewer_name"] == "Editor"
    assert review_row["reviewer_note"] == "Changed due date and owner to match meeting consensus."

