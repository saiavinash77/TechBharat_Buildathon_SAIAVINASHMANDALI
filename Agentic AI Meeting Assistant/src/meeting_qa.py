"""Evidence-backed Q&A over a meeting transcript."""

from __future__ import annotations

import os

from groq import Groq


def answer_meeting_question(transcript: str, question: str) -> str:
    if not transcript.strip():
        raise ValueError("No transcript available for this meeting.")
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is required for meeting Q&A.")

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "Answer strictly from the meeting transcript. "
                    "Include exact quotes as evidence. "
                    "If the transcript does not contain the answer, say so clearly."
                ),
            },
            {
                "role": "user",
                "content": f"Transcript:\n{transcript}\n\nQuestion: {question.strip()}",
            },
        ],
    )
    return (response.choices[0].message.content or "").strip()
