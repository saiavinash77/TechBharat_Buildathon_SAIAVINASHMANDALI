import os
from groq import Groq
import instructor
from typing import Optional

from src.state import MeetingRecord


def _get_client():
    """Create the model client only when extraction is actually requested."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is required to extract meeting data.")

    groq_client = Groq(api_key=api_key)
    try:
        return instructor.from_groq(groq_client, mode=instructor.Mode.JSON), True
    except Exception:
        return groq_client, False


def load_feedback_rules() -> list:
    import json
    path = "data/rejection_memory.json"
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return []


def _normalize_feedback(human_feedback) -> Optional[str]:
    if not human_feedback:
        return None
    if isinstance(human_feedback, dict):
        if human_feedback.get("decision") == "re_extract":
            return f"re_extract:{human_feedback.get('note', '')}"
        return None
    return str(human_feedback)


def extract_node(transcript: str, meeting_date_str: Optional[str] = None, human_feedback=None) -> MeetingRecord:
    from datetime import date
    if not meeting_date_str:
        meeting_date_str = date.today().isoformat()

    human_feedback = _normalize_feedback(human_feedback)
    feedback_rules = load_feedback_rules()
    feedback_context = ""
    if human_feedback and human_feedback.startswith("re_extract"):
        notes = human_feedback.split(":", 1)[1] if ":" in human_feedback else ""
        feedback_context = f"\nPREVIOUS EXTRACTION REJECTED. User notes: {notes}\nAvoid extracting vague items. Only concrete commitments with explicit owners."
        feedback_rules.append(notes)
        os.makedirs("data", exist_ok=True)
        import json
        with open("data/rejection_memory.json", "w") as f:
            json.dump(feedback_rules[-10:], f)

    if feedback_rules:
        feedback_context += "\nHistorical rejection patterns: " + "; ".join(feedback_rules[-5:])

    system_msg = (
        "You are a safety-first meeting assistant. Extract structured data from the transcript. "
        "For every candidate action, include its exact transcript sentence as quote_provenance and identify the speaker only if the transcript labels them. "
        "Classify each candidate strictly: EXPLICIT_COMMITMENT only when that speaker directly accepts responsibility (for example, 'I will do X'); "
        "NEEDS_CONFIRMATION for requests, proposed ownership, or unclear/unnamed ownership; DISCUSSION_ONLY for ideas, questions, and decisions without a commitment. "
        "Never invent a person, a commitment, a speaker, or a due date. Set owner_name to Unassigned unless the statement is an explicit self-commitment. "
        "owner_explicitly_accepted is true only for a direct self-commitment. "
        "Confidence measures extraction evidence, not permission to assign work. "
        "Resolve relative dates to YYYY-MM-DD using the meeting date as anchor. "
        f"{feedback_context}"
    )

    prompt = f"""Meeting Date: {meeting_date_str}

Transcript:
\"\"\"{transcript}\"\"\"

Extract:
1. Executive summary (2-3 sentences)
2. Decisions made (list)
3. Open questions (list)
4. Risks or blockers raised (list)
5. Candidate action items with classification, speaker, owner acceptance, due date mention, resolved date, priority, confidence (0.0-1.0), extraction reason, and the exact quote from transcript
"""

    try:
        client, use_instructor = _get_client()
        if use_instructor:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt},
                ],
                response_model=MeetingRecord,
                temperature=0.2,
            )
            return response
        else:
            # Fallback: raw Groq with JSON mode
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt + "\n\nRespond with valid JSON matching the MeetingRecord schema."},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            return MeetingRecord.model_validate_json(resp.choices[0].message.content)
    except Exception as e:
        return MeetingRecord(
            executive_summary=f"Extraction failed: {str(e)}",
            action_items=[],
        )
