"""Durable GCS -> Groq -> InsForge media transcription workflow."""

from __future__ import annotations

import os
from datetime import date
from uuid import uuid4

from src.insforge_client import InsForgeRepository
from src.media import GCSMediaStore, build_object_key, validate_media
from src.nodes.transcribe import TranscriptionResult, transcribe_url


def create_upload(meeting_title: str, meeting_date: date, filename: str, content_type: str, size_bytes: int) -> dict:
    validate_media(filename, content_type, size_bytes)
    store = GCSMediaStore()
    repository = InsForgeRepository()
    meeting_key = f"mtg_{uuid4().hex}"
    meeting = repository.insert("meetings", {
        "meeting_key": meeting_key,
        "title": meeting_title.strip() or "Untitled meeting",
        "meeting_date": meeting_date.isoformat(),
        "transcript_text": "",
        "transcript_hash": "0" * 64,
        "processing_status": "RECEIVED",
    })
    object_key = build_object_key(meeting_key, filename)
    media = repository.insert("media_files", {
        "meeting_id": meeting["id"],
        "storage_provider": "GCS",
        "bucket_name": store.bucket_name,
        "object_key": object_key,
        "original_filename": filename,
        "content_type": content_type,
        "size_bytes": size_bytes,
        "upload_status": "AWAITING_UPLOAD",
        "transcription_status": "NOT_STARTED",
    })
    return {"meeting": meeting, "media": media, "upload_url": store.create_upload_url(object_key, content_type)}


def confirm_upload(media_id: str) -> dict:
    repository = InsForgeRepository()
    media = repository.get_one("media_files", media_id)
    if not media:
        raise LookupError("Media file not found.")
    store = GCSMediaStore(bucket_name=media["bucket_name"])
    if not store.exists(media["object_key"]):
        raise ValueError("The media object is not present in the private GCS bucket yet.")
    return repository.update("media_files", media_id, {"upload_status": "UPLOADED"})


def transcribe_media(media_id: str) -> tuple[dict, TranscriptionResult]:
    repository = InsForgeRepository()
    media = repository.get_one("media_files", media_id)
    if not media:
        raise LookupError("Media file not found.")
    if media["upload_status"] != "UPLOADED":
        raise ValueError("Confirm the GCS upload before starting transcription.")

    repository.update("media_files", media_id, {"transcription_status": "PROCESSING"})
    try:
        store = GCSMediaStore(bucket_name=media["bucket_name"])
        try:
            signed_url = store.create_read_url(media["object_key"])
            transcription = transcribe_url(signed_url)
        except Exception:
            # Fallback to direct GCS SDK stream download for Groq Whisper
            media_bytes = store.download_bytes(media["object_key"])
            transcription = transcribe_file_bytes(media["original_filename"], media_bytes)
        repository.update("media_files", media_id, {
            "transcription_status": "COMPLETED",
            "transcription_model": os.getenv("GROQ_TRANSCRIPTION_MODEL", "whisper-large-v3-turbo"),
            "transcript_language": transcription.language,
            "duration_seconds": transcription.duration_seconds,
        })
        repository.update("meetings", media["meeting_id"], {
            "transcript_text": transcription.text,
            "processing_status": "EXTRACTING",
        })
        for segment in transcription.segments:
            repository.insert("transcript_segments", {
                "meeting_id": media["meeting_id"],
                "media_file_id": media_id,
                "segment_index": segment.index,
                "start_seconds": segment.start_seconds,
                "end_seconds": segment.end_seconds,
                "text": segment.text,
                "average_log_probability": segment.average_log_probability,
                "no_speech_probability": segment.no_speech_probability,
            })
        return media, transcription
    except Exception as error:
        repository.update("media_files", media_id, {
            "transcription_status": "FAILED",
            "transcription_error": str(error)[:2000],
        })
        raise
