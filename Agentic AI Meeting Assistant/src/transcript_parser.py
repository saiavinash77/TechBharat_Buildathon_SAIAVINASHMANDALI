"""Parse plain text, WebVTT, and SRT transcript files into normalized dialogue text."""

from __future__ import annotations

import re
from pathlib import Path


def parse_transcript_file(content: bytes, filename: str) -> str:
    text = content.decode("utf-8", errors="replace")
    suffix = Path(filename).suffix.lower()
    if suffix == ".vtt":
        return _parse_vtt(text)
    if suffix == ".srt":
        return _parse_srt(text)
    return _normalize_plain(text)


def _normalize_plain(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def _parse_vtt(text: str) -> str:
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.upper().startswith("WEBVTT") or "-->" in line or line.isdigit():
            continue
        if re.match(r"^\d{2}:\d{2}", line):
            continue
        lines.append(line)
    return _normalize_plain("\n".join(lines))


def _parse_srt(text: str) -> str:
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.isdigit() or "-->" in line:
            continue
        if re.match(r"^\d{2}:\d{2}", line):
            continue
        lines.append(line)
    return _normalize_plain("\n".join(lines))
