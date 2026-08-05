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


def validate_media(filename: str, content_type: str, size_bytes: int) -> None:
    if not filename or Path(filename).name != filename:
        raise ValueError("filename must be a simple file name")
    if content_type not in SUPPORTED_CONTENT_TYPES:
        raise ValueError("Unsupported media type. Use MP3, WAV, M4A, MP4, WebM, OGG, or FLAC.")
    if size_bytes <= 0 or size_bytes > max_upload_bytes():
        raise ValueError(f"Media must be between 1 byte and {max_upload_bytes()} bytes.")


def build_object_key(meeting_key: str, filename: str) -> str:
    safe_meeting_key = re.sub(r"[^a-zA-Z0-9_-]", "-", meeting_key).strip("-") or "meeting"
    return f"meetings/{safe_meeting_key}/{uuid4().hex}{Path(filename).suffix.lower()}"


class GCSMediaStore:
    """Uses a private GCS bucket; raw media never passes through InsForge storage."""

    def __init__(self, bucket_name: str | None = None, project_id: str | None = None, client=None):
        self.bucket_name = bucket_name or os.getenv("GCS_MEDIA_BUCKET")
        if not self.bucket_name:
            raise MediaConfigurationError("GCS_MEDIA_BUCKET is required for media uploads.")
        self.client = client or storage.Client(project=project_id or os.getenv("GCP_PROJECT_ID"))
        self.bucket = self.client.bucket(self.bucket_name)

    @property
    def signed_url_ttl(self) -> timedelta:
        try:
            minutes = int(os.getenv("MEDIA_SIGNED_URL_TTL_MINUTES", "15"))
        except ValueError as error:
            raise MediaConfigurationError("MEDIA_SIGNED_URL_TTL_MINUTES must be an integer") from error
        return timedelta(minutes=max(1, min(minutes, 60)))

    def create_upload_url(self, object_key: str, content_type: str) -> str:
        return self.bucket.blob(object_key).generate_signed_url(
            version="v4", expiration=self.signed_url_ttl, method="PUT", content_type=content_type,
        )

    def create_read_url(self, object_key: str) -> str:
        return self.bucket.blob(object_key).generate_signed_url(
            version="v4", expiration=self.signed_url_ttl, method="GET",
        )

    def exists(self, object_key: str) -> bool:
        return self.bucket.blob(object_key).exists()
