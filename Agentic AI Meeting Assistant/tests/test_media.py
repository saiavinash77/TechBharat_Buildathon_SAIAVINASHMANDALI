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


class DummyClient:
    def __init__(self, credentials):
        self._credentials = credentials
        self.bucket = lambda name: None


class SigningCredentials:
    def __init__(self):
        self.signer_email = "svc-account@project.iam.gserviceaccount.com"

    def sign_bytes(self, value):
        return b"dummy-signature"


class RefreshCredentials:
    def __init__(self):
        self.token = None
        self.expired = True
        self.refreshed = False

    def refresh(self, request):
        self.token = "refreshed-token"
        self.expired = False
        self.refreshed = True


class RefreshFailsCredentials(RefreshCredentials):
    def refresh(self, request):
        raise RuntimeError("refresh failed")


def test_signing_kwargs_uses_local_signer_when_available():
    from src.media import GCSMediaStore

    credentials = SigningCredentials()
    client = DummyClient(credentials)
    store = GCSMediaStore(bucket_name="test-bucket", project_id="test-project", service_account_email="svc-account@project.iam.gserviceaccount.com", client=client)

    assert store._signing_kwargs() == {"service_account_email": "svc-account@project.iam.gserviceaccount.com"}


def test_signing_kwargs_refreshes_token_for_user_adc():
    from src.media import GCSMediaStore

    credentials = RefreshCredentials()
    client = DummyClient(credentials)
    store = GCSMediaStore(bucket_name="test-bucket", project_id="test-project", service_account_email="svc-account@project.iam.gserviceaccount.com", client=client)

    kwargs = store._signing_kwargs()

    assert kwargs == {
        "service_account_email": "svc-account@project.iam.gserviceaccount.com",
        "access_token": "refreshed-token",
    }
    assert credentials.refreshed is True


def test_signing_kwargs_uses_gcloud_access_token_fallback(monkeypatch):
    import src.media as media
    from src.media import GCSMediaStore

    credentials = RefreshFailsCredentials()
    client = DummyClient(credentials)
    store = GCSMediaStore(bucket_name="test-bucket", project_id="test-project", service_account_email="svc-account@project.iam.gserviceaccount.com", client=client)

    monkeypatch.setattr(media.shutil, 'which', lambda path: 'C:/Program Files/gcloud/bin/gcloud')
    monkeypatch.setattr(media.subprocess, 'check_output', lambda args, stderr, text, timeout: 'gcloud-access-token')

    kwargs = store._signing_kwargs()

    assert kwargs == {
        "service_account_email": "svc-account@project.iam.gserviceaccount.com",
        "access_token": "gcloud-access-token",
    }
