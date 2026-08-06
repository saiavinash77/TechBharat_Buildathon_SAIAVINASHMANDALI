from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

from src.state import AgentState
from src.nodes.extract import extract_node
from src.nodes.resolve import resolve_node
from src.nodes.dedup import dedup_node
from src.nodes.execute import execute_node
from src.nodes.audit import audit_node


def node_extract(state: AgentState):
    # Pass human_feedback so re-extraction loops actually improve
    result = extract_node(
        state["transcript"],
        state.get("meeting_date"),
        human_feedback=state.get("human_feedback")
    )
    return {"extracted": result}


def node_resolve(state: AgentState):
    if not state.get("extracted"):
        return {"error": "Nothing to resolve"}
    result = resolve_node(
        state["extracted"],
        state.get("meeting_date", ""),
    )
    return {"extracted": result}


def node_review(state: AgentState):
    """Pause until a reviewer supplies a structured decision."""
    extracted = state.get("extracted")
    proposed_items = [item.model_dump() for item in extracted.action_items] if extracted else []
    decision = interrupt({
        "type": "review_required",
        "meeting_id": state.get("meeting_id"),
        "summary": extracted.executive_summary if extracted else "",
        "decisions": extracted.decisions_made if extracted else [],
        "open_questions": extracted.open_questions if extracted else [],
        "risks_or_blockers": getattr(extracted, "risks_or_blockers", []) if extracted else [],
        "items": proposed_items,
        "rules": {
            "explicit_commitment": "May be assigned only when the speaker directly accepted it.",
            "needs_confirmation": "May be sent to GitHub unassigned with needs-confirmation.",
            "discussion_only": "Must not be sent to GitHub.",
        },
    })
    if not isinstance(decision, dict):
        return {"human_feedback": {"decision": "reject", "note": "Invalid reviewer response"}}
    return {
        "human_feedback": decision,
        "approved_items": decision.get("approved_items", []),
    }


def route_after_review(state: AgentState) -> str:
    feedback = state.get("human_feedback") or {}
    decision = feedback.get("decision", "") if isinstance(feedback, dict) else ""
    if decision == "approve":
        return "dedup"
    if decision == "re_extract":
        return "extract"
    return "end"


def node_dedup(state: AgentState):
    items = state.get("approved_items", [])
    if not items:
        return {"action_hashes": [], "execution_results": []}
    hashes, filtered = dedup_node(state.get("meeting_id", ""), items)
    return {"action_hashes": hashes, "approved_items": filtered}


def node_execute(state: AgentState):
    items = state.get("approved_items", [])
    hashes = state.get("action_hashes", [])
    if not items:
        return {"execution_results": []}
    results = execute_node(state.get("meeting_id", ""), items, hashes)
    return {"execution_results": results}


def node_audit(state: AgentState):
    items = state.get("approved_items", [])
    hashes = state.get("action_hashes", [])
    results = state.get("execution_results", [])
    if items and hashes and results:
        audit_node(state.get("meeting_id", ""), items, hashes, results)
    return state


# Build graph
builder = StateGraph(AgentState)

builder.add_node("extract", node_extract)
builder.add_node("resolve", node_resolve)
builder.add_node("review", node_review)
builder.add_node("dedup", node_dedup)
builder.add_node("execute", node_execute)
builder.add_node("audit", node_audit)

builder.set_entry_point("extract")
builder.add_edge("extract", "resolve")
builder.add_edge("resolve", "review")

builder.add_conditional_edges(
    "review",
    route_after_review,
    {"dedup": "dedup", "extract": "extract", "end": END},
)

builder.add_edge("dedup", "execute")
builder.add_edge("execute", "audit")
builder.add_edge("audit", END)

# Compile with in-memory checkpoints (swap to PostgresSaver for production)
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)
