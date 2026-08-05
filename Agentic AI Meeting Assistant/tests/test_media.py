from types import SimpleNamespace

import pytest

from src.media import build_object_key, validate_media
from src.nodes.transcribe import _normalise_result


def test_media_key_does_not_leak_the_original_filename():
    key = build_object_key("meeting / 1", "standup.mp4")

    assert key.startswith("meetings/meeting---1/")
    assert key.endswith(".mp4")
    assert "standup" not in key


def test_media_validation_rejects_untrusted_or_large_uploads(monkeypatch):
    monkeypatch.setenv("MEDIA_MAX_UPLOAD_BYTES", "10")

    with pytest.raises(ValueError):
        validate_media("../secret.mp3", "audio/mpeg", 1)
    with pytest.raises(ValueError):
        validate_media("meeting.mp3", "audio/mpeg", 11)


def test_verbose_groq_response_preserves_timestamp_evidence():
    response = SimpleNamespace(
        text="I will prepare the demo.",
        language="en",
        duration=5.0,
        segments=[SimpleNamespace(id=3, start=1.2, end=4.5, text=" I will prepare the demo. ", avg_logprob=-0.1, no_speech_prob=0.01)],
    )

    result = _normalise_result(response)

    assert result.text == "I will prepare the demo."
    assert result.segments[0].index == 3
    assert result.segments[0].start_seconds == 1.2
