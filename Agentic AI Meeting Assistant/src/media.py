"""Private GCS media storage helpers used by the server-side workflow."""

from __future__ import annotations

import os
import re
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

from google.cloud import storage


class MediaConfigurationError(RuntimeError):
    """Raised when a required server-side media setting is missing."""


SUPPORTED_CONTENT_TYPES = {
    "audio/flac", "audio/m4a", "audio/mp4", "audio/mpeg", "audio/ogg",
    "audio/wav", "audio/webm", "video/mp4", "video/webm",
}
DEFAULT_MAX_UPLOAD_BYTES = 500 * 1024 * 1024


def max_upload_bytes() -> int:
    value = os.getenv("MEDIA_MAX_UPLOAD_BYTES", str(DEFAULT_MAX_UPLOAD_BYTES))
    try:
        return int(value)
    except ValueError as error:
        raise MediaConfigurationError("MEDIA_MAX_UPLOAD_BYTES must be an integer") from error


def validate_media(filename: str, content_type: str, size_bytes: int | str) -> None:
    if not filename or Path(filename).name != filename or "/" in filename or "\\" in filename:
        raise ValueError("filename must be a simple file name")
    if content_type not in SUPPORTED_CONTENT_TYPES:
        raise ValueError("Unsupported media type. Use MP3, WAV, M4A, MP4, WebM, OGG, or FLAC.")
    try:
        size_int = int(size_bytes)
    except (ValueError, TypeError) as error:
        raise ValueError("size_bytes must be a valid integer.") from error
    if size_int <= 0 or size_int > max_upload_bytes():
        raise ValueError(f"Media must be between 1 byte and {max_upload_bytes()} bytes.")


def build_object_key(meeting_key: str, filename: str) -> str:
    safe_meeting_key = re.sub(r"[^a-zA-Z0-9_-]", "-", meeting_key).strip("-") or "meeting"
    return f"meetings/{safe_meeting_key}/{uuid4().hex}{Path(filename).suffix.lower()}"


class GCSMediaStore:
    """Uses a private GCS bucket; raw media never passes through InsForge storage.

    Two supported authentication modes (no code changes required to switch):

    MODE A — SA JSON key (traditional): set ``GOOGLE_APPLICATION_CREDENTIALS`` env var
    to the absolute path of a service account JSON key file. The SDK signs URLs
    locally using the private key embedded in the JSON.

    MODE B — User ADC + IAM SignBlob (org-policy-safe, recommended here):
    1. Run ``gcloud auth application-default login`` once on your machine. This
       stores your user credentials at ``%APPDATA%\\gcloud\\application_default_credentials.json``.
    2. Set ``GCS_SERVICE_ACCOUNT_EMAIL`` to the meeting-assistant service account email.
       The SDK calls the GCP IAM ``signBlob`` API on your behalf to mint signed URLs
       as that service account. No SA JSON key file ever touches disk.
       Required IAM: your user must have ``iam.serviceAccounts.signBlob`` on the SA
       (inherited via Project Owner) and the SA itself must have ``roles/storage.objectAdmin``
       scoped to this bucket (least-privilege, project-wide Owner also works).
    """

    def __init__(
        self,
        bucket_name: str | None = None,
        project_id: str | None = None,
        service_account_email: str | None = None,
        client=None,
    ):
        self.bucket_name = bucket_name or os.getenv("GCS_MEDIA_BUCKET")
        if not self.bucket_name:
            raise MediaConfigurationError("GCS_MEDIA_BUCKET is required for media uploads.")
        self.service_account_email = service_account_email or os.getenv("GCS_SERVICE_ACCOUNT_EMAIL")
        resolved_project = project_id or os.getenv("GCP_PROJECT_ID")
        self.client = client or storage.Client(project=resolved_project)
        self.bucket = self.client.bucket(self.bucket_name)

    @property
    def signed_url_ttl(self) -> timedelta:
        try:
            minutes = int(os.getenv("MEDIA_SIGNED_URL_TTL_MINUTES", "15"))
        except ValueError as error:
            raise MediaConfigurationError("MEDIA_SIGNED_URL_TTL_MINUTES must be an integer") from error
        return timedelta(minutes=max(1, min(minutes, 60)))

    def _signing_kwargs(self) -> dict[str, str]:
        if self.service_account_email:
            return {"service_account_email": self.service_account_email}
        return {}

    def create_upload_url(self, object_key: str, content_type: str) -> str:
        return self.bucket.blob(object_key).generate_signed_url(
            version="v4",
            expiration=self.signed_url_ttl,
            method="PUT",
            content_type=content_type,
            **self._signing_kwargs(),
        )

    def create_read_url(self, object_key: str) -> str:
        return self.bucket.blob(object_key).generate_signed_url(
            version="v4",
            expiration=self.signed_url_ttl,
            method="GET",
            **self._signing_kwargs(),
        )

    def exists(self, object_key: str) -> bool:
        return self.bucket.blob(object_key).exists()
