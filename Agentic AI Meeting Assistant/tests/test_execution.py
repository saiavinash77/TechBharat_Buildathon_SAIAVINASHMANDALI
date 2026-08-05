from src.nodes.dedup import generate_action_hash
from src.nodes.execute import execute_github_issue


def test_action_hash_is_stable_across_cosmetic_changes():
    first = generate_action_hash(" Meeting-1 ", " Rahul ", "Finish API")
    second = generate_action_hash("meeting-1", "rahul", "finish api")

    assert first == second


def test_github_execution_is_safe_in_dry_run(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")

    result = execute_github_issue("Finish API", "Evidence from the meeting")

    assert result["success"] is True
    assert result["dry_run"] is True
    assert "Finish API" in result["issue_url"]
