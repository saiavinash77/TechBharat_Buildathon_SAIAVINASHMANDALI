from fastapi.testclient import TestClient

import main
from main import app


def test_empty_transcript_review_payload_is_helpful():
    payload = main._build_empty_transcript_review_payload("meeting-123", "   ")

    assert payload["type"] == "review_required"
    assert payload["items"] == []
    assert "No speech was detected" in payload["summary"]
    assert payload["empty_reason"] == "empty_transcript"


def test_health_endpoint_is_available_without_model_credentials():
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ingest_pauses_at_a_native_review_interrupt_without_model_credentials():
    response = TestClient(app).post("/ingest", json={
        "transcript": "We discussed the roadmap and will decide next week.",
        "meeting_date": "2026-08-05",
        "meeting_id": "native-interrupt-test",
    })

    assert response.status_code == 200
    assert response.json()["status"] == "waiting_for_review"
    assert response.json()["review"]["type"] == "review_required"


def test_ingest_returns_graceful_extraction_failed_status_without_crashing(monkeypatch):
    """If the graph ends without reaching the LangGraph interrupt (no review payload)
    the endpoint must not IndexError. A descriptive status is returned instead."""

    class FakeSnapshot:
        tasks = []           # simulate graph that ran to END with no interrupt
        values = {"error": None}
        next_config = None

    monkeypatch.setattr(main.graph, "get_state", lambda _config: FakeSnapshot())

    resp = TestClient(app).post("/ingest", json={
        "transcript": "Alpha bravo charlie delta.",
        "meeting_date": "2026-08-06",
        "meeting_id": "fail-safe-test",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "extraction_failed"
    assert body["thread_id"] == "fail-safe-test"
    assert "Extraction did not produce reviewable candidates" in body["error"]

