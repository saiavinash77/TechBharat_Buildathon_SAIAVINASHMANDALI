from fastapi.testclient import TestClient

from main import app


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
