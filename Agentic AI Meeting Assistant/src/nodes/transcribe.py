import os
from typing import Any

from groq import Groq
from pydantic import BaseModel, Field


def _get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is required to transcribe audio.")
    return Groq(api_key=api_key)


class TranscriptSegment(BaseModel):
    index: int
    start_seconds: float
    end_seconds: float
    text: str
    average_log_probability: float | None = None
    no_speech_probability: float | None = None


class TranscriptionResult(BaseModel):
    text: str
    language: str | None = None
    duration_seconds: float | None = None
    segments: list[TranscriptSegment] = Field(default_factory=list)


def _value(source: Any, key: str, default: Any = None) -> Any:
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _normalise_result(response: Any) -> TranscriptionResult:
    segments = []
    for index, segment in enumerate(_value(response, "segments", []) or []):
        segments.append(TranscriptSegment(
            index=int(_value(segment, "id", index)),
            start_seconds=float(_value(segment, "start", 0)),
            end_seconds=float(_value(segment, "end", 0)),
            text=str(_value(segment, "text", "")).strip(),
            average_log_probability=_value(segment, "avg_logprob"),
            no_speech_probability=_value(segment, "no_speech_prob"),
        ))
    return TranscriptionResult(
        text=str(_value(response, "text", "")).strip(),
        language=_value(response, "language"),
        duration_seconds=_value(response, "duration"),
        segments=segments,
    )


def _transcribe(**source: Any) -> TranscriptionResult:
    response = _get_groq_client().audio.transcriptions.create(
        model=os.getenv("GROQ_TRANSCRIPTION_MODEL", "whisper-large-v3-turbo"),
        response_format="verbose_json",
        timestamp_granularities=["segment", "word"],
        temperature=0,
        **source,
    )
    return _normalise_result(response)


def transcribe_audio(audio_path: str) -> TranscriptionResult:
    """Transcribe a local audio/video file without translating its language."""
    if not os.path.exists(audio_path):
        raise FileNotFoundError(audio_path)
    with open(audio_path, "rb") as media_file:
        return _transcribe(file=media_file)


def transcribe_url(media_url: str) -> TranscriptionResult:
    """Transcribe a short-lived signed media URL and retain timestamp evidence."""
    if not media_url.startswith(("https://", "http://")):
        raise ValueError("media_url must be an HTTP(S) URL")
    return _transcribe(url=media_url)


def transcribe_file_bytes(filename: str, content: bytes) -> TranscriptionResult:
    """Transcribe binary file bytes directly from GCS media store."""
    return _transcribe(file=(filename, content))
