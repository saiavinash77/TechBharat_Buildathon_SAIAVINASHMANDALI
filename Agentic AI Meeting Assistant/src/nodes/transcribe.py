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
    """Transcribe binary file bytes directly from GCS media store with automatic chunking for large files (>19MB)."""
    CHUNK_SIZE = 19 * 1024 * 1024
    if len(content) <= CHUNK_SIZE:
        return _transcribe(file=(filename, content))

    all_text = []
    all_segments = []
    total_duration = 0.0
    seg_counter = 0

    for i in range(0, len(content), CHUNK_SIZE):
        chunk_data = content[i : i + CHUNK_SIZE]
        chunk_name = f"chunk_{i // CHUNK_SIZE}_{filename}"
        try:
            res = _transcribe(file=(chunk_name, chunk_data))
            if res.text:
                all_text.append(res.text)
            for seg in res.segments:
                seg.index = seg_counter
                seg.start_seconds += total_duration
                seg.end_seconds += total_duration
                all_segments.append(seg)
                seg_counter += 1
            if res.duration_seconds:
                total_duration += res.duration_seconds
        except Exception as error:
            # If a trailing chunk fails, continue with already transcribed segments
            if not all_text:
                raise error
            break

    return TranscriptionResult(
        text=" ".join(all_text),
        duration_seconds=total_duration,
        segments=all_segments,
    )
