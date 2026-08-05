from src.nodes import execute


def test_discussion_only_item_cannot_be_sent_to_github(monkeypatch):
    called = False

    def fake_dispatch(*args, **kwargs):
        nonlocal called
        called = True
        return {"success": True}

    monkeypatch.setattr(execute, "execute_github_issue", fake_dispatch)

    results = execute.execute_node("meeting-1", [{"action_title": "Consider dark mode", "classification": "DISCUSSION_ONLY"}], ["hash"])

    assert called is False
    assert results[0]["skipped"] is True


def test_needs_confirmation_is_never_assigned(monkeypatch):
    captured = {}

    def fake_dispatch(**kwargs):
        captured.update(kwargs)
        return {"success": True}

    monkeypatch.setattr(execute, "execute_github_issue", fake_dispatch)
    execute.execute_node("meeting-1", [{
        "action_title": "Review the proposal",
        "classification": "NEEDS_CONFIRMATION",
        "owner_name": "Asha",
        "speaker_name": "Ravi",
        "priority": "MEDIUM",
        "quote_provenance": "Can Asha review the proposal?",
        "github_assignee_login": "asha",
    }], ["hash"])

    assert "needs-confirmation" in captured["labels"]
    assert captured["assignees"] == []
