import os
from datetime import date

import chainlit as cl
from dotenv import load_dotenv
from groq import Groq
from langgraph.types import Command

from src.graph import graph
from src.media_workflow import create_upload, confirm_upload, transcribe_media
from src.models import init_db
from src.state import AgentState

load_dotenv()
init_db()


def _groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")
    return Groq(api_key=api_key)


async def _start_review(transcript: str, meeting_date: str, meeting_id: str):
    state: AgentState = {
        "transcript": transcript,
        "meeting_date": meeting_date,
        "meeting_id": meeting_id,
        "approved_items": [],
        "rejected_items": [],
        "action_hashes": [],
        "execution_results": [],
    }
    config = {"configurable": {"thread_id": meeting_id}}
    graph.invoke(state, config)
    cl.user_session.set("thread_id", meeting_id)
    cl.user_session.set("transcript", transcript)
    snapshot = graph.get_state(config)
    extracted = snapshot.values.get("extracted") if snapshot else None
    if not extracted:
        await cl.Message(content="Extraction did not return any reviewable data.").send()
        return
    await _show_extraction(extracted)


@cl.on_chat_start
async def start():
    await cl.Message(
        content="Agentic AI Meeting Assistant\n\nPaste a transcript, ask a question about the current meeting, or use `/upload` for a small audio/video file. Large files use the signed-upload API."
    ).send()


@cl.on_message
async def main(message: cl.Message):
    text = message.content.strip()
    thread_id = cl.user_session.get("thread_id")
    awaiting = cl.user_session.get("awaiting_feedback", False)

    if text == "/upload":
        files = await cl.AskFileMessage(
            content="Upload one MP3, WAV, M4A, MP4, WebM, OGG, or FLAC file (up to 100 MB in this UI).",
            accept={
                "audio/mpeg": [".mp3"], "audio/wav": [".wav"], "audio/mp4": [".m4a"],
                "video/mp4": [".mp4"], "audio/webm": [".webm"], "video/webm": [".webm"],
                "audio/ogg": [".ogg"], "audio/flac": [".flac"],
            },
            max_size_mb=100,
            timeout=120,
        ).send()
        if not files:
            return
        uploaded = files[0]
        try:
            upload = create_upload("Uploaded meeting", date.today(), uploaded.name, uploaded.mime or "audio/mpeg", uploaded.size or 0)
            # The Chainlit UI has the file locally; upload it directly to the signed URL.
            import requests
            with open(uploaded.path, "rb") as media_file:
                response = requests.put(upload["upload_url"], data=media_file, headers={"Content-Type": uploaded.mime or "audio/mpeg"}, timeout=120)
            response.raise_for_status()
            confirm_upload(upload["media"]["id"])
            _, transcription = transcribe_media(upload["media"]["id"])
            await _start_review(transcription.text, date.today().isoformat(), upload["meeting"]["meeting_key"])
        except Exception as error:
            await cl.Message(content=f"Media upload failed: {error}").send()
        return

    if awaiting:
        cl.user_session.set("awaiting_feedback", False)
        if thread_id:
            graph.invoke(Command(resume={"decision": "re_extract", "note": text, "approved_items": []}), {"configurable": {"thread_id": thread_id}})
            snapshot = graph.get_state({"configurable": {"thread_id": thread_id}})
            if snapshot and snapshot.values.get("extracted"):
                await _show_extraction(snapshot.values["extracted"])
        return

    if text.endswith("?") and thread_id:
        transcript = cl.user_session.get("transcript", "")
        try:
            response = _groq_client().chat.completions.create(
                model="llama-3.3-70b-versatile",
                temperature=0,
                messages=[
                    {"role": "system", "content": "Answer only from the supplied meeting transcript. If evidence is absent, say so. Include the exact supporting quote."},
                    {"role": "user", "content": f"Transcript:\n{transcript}\n\nQuestion: {text}"},
                ],
            )
            await cl.Message(content=f"Answer:\n{response.choices[0].message.content}").send()
        except Exception as error:
            await cl.Message(content=f"Question answering failed: {error}").send()
        return

    if text.startswith("/status"):
        await cl.Message(content=f"Active meeting: `{thread_id}`" if thread_id else "No active meeting.").send()
        return

    if len(text) > 50:
        await cl.Message(content="Extracting meeting candidates...").send()
        await _start_review(text, date.today().isoformat(), f"mtg_{abs(hash(text)) % 100000}")
        return

    await cl.Message(content="Paste a transcript, ask a question about the active meeting, or use `/upload`.").send()


async def _show_extraction(extracted):
    pending_actions = []
    message = "## Review meeting candidates\n\n"
    for index, item in enumerate(extracted.action_items):
        message += (
            f"**{index + 1}. {item.action_title}**\n"
            f"Class: `{item.classification}` | Speaker: `{item.speaker_name}` | Owner: `{item.owner_name}`\n"
            f"Quote: _{item.quote_provenance}_\n\n"
        )
        if item.classification in {"EXPLICIT_COMMITMENT", "NEEDS_CONFIRMATION"}:
            pending_actions.append(item.model_dump())
    cl.user_session.set("pending_actions", pending_actions)
    await cl.Message(content=message).send()
    await cl.Message(content="Review the candidates before dispatch.", actions=[
        cl.Action(name="approve_all", value="approve", label="Approve eligible", collapsed=False),
        cl.Action(name="reject_all", value="reject", label="Reject", collapsed=False),
        cl.Action(name="re_extract", value="re_extract", label="Re-extract", collapsed=False),
    ]).send()


@cl.action_callback("approve_all")
async def on_approve(action):
    thread_id = cl.user_session.get("thread_id")
    pending = cl.user_session.get("pending_actions", [])
    if not thread_id:
        return
    graph.invoke(Command(resume={"decision": "approve", "approved_items": pending}), {"configurable": {"thread_id": thread_id}})
    snapshot = graph.get_state({"configurable": {"thread_id": thread_id}})
    results = snapshot.values.get("execution_results", []) if snapshot else []
    await cl.Message(content=f"Completed {sum(bool(r.get('success')) for r in results)}/{len(results)} approved dispatches.").send()


@cl.action_callback("reject_all")
async def on_reject(action):
    thread_id = cl.user_session.get("thread_id")
    if thread_id:
        graph.invoke(Command(resume={"decision": "reject", "approved_items": []}), {"configurable": {"thread_id": thread_id}})
    await cl.Message(content="Rejected. No GitHub side effects were triggered.").send()


@cl.action_callback("re_extract")
async def on_re_extract(action):
    cl.user_session.set("awaiting_feedback", True)
    await cl.Message(content="Send the correction, for example: `ignore vague items`.").send()
