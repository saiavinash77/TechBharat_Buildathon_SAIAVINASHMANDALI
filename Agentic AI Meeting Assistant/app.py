import os
from datetime import date

import chainlit as cl
from dotenv import load_dotenv
from groq import Groq
from langgraph.types import Command

from src.graph import graph
from src.media_workflow import create_upload, confirm_upload, transcribe_media
from src.durable_workflow import persist_candidates, review_candidate, dispatch_approved_candidates
from src.insforge_client import InsForgeRepository
from src.state import AgentState

load_dotenv()


def _groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured in .env.")
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
        await cl.Message(content="⚠️ Extraction did not return any reviewable data. Check your transcript or GROQ API key.").send()
        return
    
    # Persist durable candidates to InsForge Postgres DB
    try:
        repository = InsForgeRepository()
        candidates = persist_candidates(repository, meeting_id, meeting_id, extracted.action_items)
        cl.user_session.set("candidates", candidates)
    except Exception:
        candidates = [item.model_dump() for item in extracted.action_items]
        cl.user_session.set("candidates", candidates)

    await _show_extraction(extracted, candidates)


@cl.on_chat_start
async def start():
    await cl.Message(
        content=(
            "### 🎙️ Agentic AI Meeting Assistant\n\n"
            "Paste a meeting transcript below, ask a question about the meeting, or use `/upload` to upload an audio/video recording.\n\n"
            "*Safety-First*: AI extracts candidates with timestamp evidence, but no GitHub issues are created without your explicit approval."
        )
    ).send()


@cl.on_message
async def main(message: cl.Message):
    text = message.content.strip()
    thread_id = cl.user_session.get("thread_id")
    awaiting = cl.user_session.get("awaiting_feedback", False)

    if text == "/upload":
        files = await cl.AskFileMessage(
            content="Upload a meeting recording (MP3, WAV, M4A, MP4, WebM, OGG, or FLAC file up to 100 MB).",
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
            await cl.Message(content=f"⏳ Preparing private upload for `{uploaded.name}`...").send()
            upload = create_upload("Uploaded meeting", date.today(), uploaded.name, uploaded.mime or "audio/mpeg", uploaded.size or 0)
            
            import requests
            with open(uploaded.path, "rb") as media_file:
                response = requests.put(upload["upload_url"], data=media_file, headers={"Content-Type": uploaded.mime or "audio/mpeg"}, timeout=120)
            response.raise_for_status()
            confirm_upload(upload["media"]["id"])
            
            await cl.Message(content="🎙️ Transcribing media via Groq Whisper...").send()
            _, transcription = transcribe_media(upload["media"]["id"])
            await _start_review(transcription.text, date.today().isoformat(), upload["meeting"]["meeting_key"])
        except Exception as error:
            await cl.Message(content=f"❌ Media upload failed: {error}").send()
        return

    if awaiting:
        cl.user_session.set("awaiting_feedback", False)
        if thread_id:
            graph.invoke(Command(resume={"decision": "re_extract", "note": text, "approved_items": []}), {"configurable": {"thread_id": thread_id}})
            snapshot = graph.get_state({"configurable": {"thread_id": thread_id}})
            if snapshot and snapshot.values.get("extracted"):
                candidates = cl.user_session.get("candidates", [])
                await _show_extraction(snapshot.values["extracted"], candidates)
        return

    if text.endswith("?") and thread_id:
        transcript = cl.user_session.get("transcript", "")
        try:
            response = _groq_client().chat.completions.create(
                model="llama-3.3-70b-versatile",
                temperature=0,
                messages=[
                    {"role": "system", "content": "Answer strictly from the meeting transcript. Include exact quotes for evidence. If evidence is missing, state so clearly."},
                    {"role": "user", "content": f"Transcript:\n{transcript}\n\nQuestion: {text}"},
                ],
            )
            await cl.Message(content=f"**Answer (Evidence-Backed)**:\n\n{response.choices[0].message.content}").send()
        except Exception as error:
            await cl.Message(content=f"❌ Question answering failed: {error}").send()
        return

    if text.startswith("/status"):
        await cl.Message(content=f"📌 Active meeting thread: `{thread_id}`" if thread_id else "No active meeting thread.").send()
        return

    if len(text) > 50:
        await cl.Message(content="🧠 Analyzing transcript and extracting action candidates...").send()
        meeting_key = f"mtg_{abs(hash(text)) % 100000}"
        await _start_review(text, date.today().isoformat(), meeting_key)
        return

    await cl.Message(content="Paste a meeting transcript (>50 chars), ask a question ending in `?`, or type `/upload`.").send()


async def _show_extraction(extracted, candidates: list):
    pending_actions = []
    message = "## 📋 Review Extracted Action Candidates\n\n"
    
    if hasattr(extracted, "executive_summary") and extracted.executive_summary:
        message += f"**Executive Summary**: {extracted.executive_summary}\n\n"

    for index, item in enumerate(extracted.action_items):
        item_dict = item.model_dump() if hasattr(item, "model_dump") else item
        classification = item_dict.get("classification", "UNKNOWN")
        badge = "🟢 Commitment" if classification == "EXPLICIT_COMMITMENT" else ("🟡 Needs Review" if classification == "NEEDS_CONFIRMATION" else "🔴 Discussion Only")
        
        message += (
            f"### {index + 1}. {item_dict.get('action_title')}\n"
            f"- **Status**: {badge}\n"
            f"- **Speaker**: `{item_dict.get('speaker_name', 'Unknown')}` | **Owner**: `{item_dict.get('owner_name', 'Unassigned')}`\n"
            f"- **Evidence**: _{item_dict.get('quote_provenance', 'N/A')}_\n\n"
        )
        if classification in {"EXPLICIT_COMMITMENT", "NEEDS_CONFIRMATION"}:
            pending_actions.append(item_dict)

    cl.user_session.set("pending_actions", pending_actions)
    await cl.Message(content=message).send()
    
    await cl.Message(
        content="Choose an action to manage these candidate items before GitHub dispatch:",
        actions=[
            cl.Action(name="approve_all", value="approve", label="✅ Approve Eligible Items", collapsed=False),
            cl.Action(name="reject_all", value="reject", label="❌ Reject All", collapsed=False),
            cl.Action(name="re_extract", value="re_extract", label="🔄 Re-extract with Instructions", collapsed=False),
        ]
    ).send()


@cl.action_callback("approve_all")
async def on_approve(action):
    thread_id = cl.user_session.get("thread_id")
    pending = cl.user_session.get("pending_actions", [])
    if not thread_id:
        await cl.Message(content="⚠️ No active meeting thread found.").send()
        return
        
    graph.invoke(Command(resume={"decision": "approve", "approved_items": pending}), {"configurable": {"thread_id": thread_id}})
    snapshot = graph.get_state({"configurable": {"thread_id": thread_id}})
    results = snapshot.values.get("execution_results", []) if snapshot else []
    
    successes = sum(bool(r.get("success")) for r in results)
    total = len(results)
    
    msg = f"### 🚀 Dispatch Execution Complete ({successes}/{total} successful)\n\n"
    for r in results:
        status_icon = "✅" if r.get("success") else "❌"
        msg += f"- {status_icon} **{r.get('title', 'Action')}**: `{r.get('status', 'PENDING')}` -> Issue #{r.get('issue_number', 'DRY-RUN')} ({r.get('html_url', 'No URL')})\n"
        
    await cl.Message(content=msg).send()


@cl.action_callback("reject_all")
async def on_reject(action):
    thread_id = cl.user_session.get("thread_id")
    if thread_id:
        graph.invoke(Command(resume={"decision": "reject", "approved_items": []}), {"configurable": {"thread_id": thread_id}})
    await cl.Message(content="🛑 Candidate items rejected. No GitHub side effects or issues were created.").send()


@cl.action_callback("re_extract")
async def on_re_extract(action):
    cl.user_session.set("awaiting_feedback", True)
    await cl.Message(content="💬 Type your extraction feedback or correction instruction (e.g., `Only extract items assigned to Avinash`).").send()
