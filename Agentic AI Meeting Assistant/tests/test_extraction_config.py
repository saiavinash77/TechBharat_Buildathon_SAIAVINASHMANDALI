from src.nodes.extract import extract_node


def test_extraction_reports_missing_model_credentials_without_crashing(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    result = extract_node("A short meeting transcript.", "2026-08-05")

    assert result.action_items == []
    assert "GROQ_API_KEY" in result.executive_summary
