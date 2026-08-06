#!/usr/bin/env python3
"""Quick local test of the pipeline without Chainlit/FastAPI."""

import os
from dotenv import load_dotenv

load_dotenv()
os.makedirs("data", exist_ok=True)

from src.graph import graph
from src.state import AgentState


def load_sample() -> str:
    with open("data/sample_transcript.txt", "r") as f:
        return f.read()


def main():
    print("=" * 60)
    print("AGENTIC AI MEETING ASSISTANT — LOCAL TEST")
    print("=" * 60)

    transcript = load_sample()
    meeting_id = "test_001"

    state: AgentState = {
        "transcript": transcript,
        "meeting_date": "2026-08-05",
        "meeting_id": meeting_id,
        "approved_items": [],
        "rejected_items": [],
        "action_hashes": [],
        "execution_results": [],
    }

    config = {"configurable": {"thread_id": meeting_id}}

    # Run until review interrupt
    print("\n[1] Running extraction + resolution...")
    try:
        for event in graph.stream(state, config, stream_mode="values"):
            pass
    except Exception:
        pass

    # Pull final state
    snapshot = graph.get_state(config)
    if not snapshot:
        print("❌ Graph failed.")
        return

    extracted = snapshot.values.get("extracted")
    if not extracted:
        print("❌ No extraction result.")
        return

    print(f"\n[2] Summary: {extracted.executive_summary}\n")
    print(f"Decisions: {extracted.decisions_made}\n")
    print(f"Open Questions: {extracted.open_questions}\n")
    print("[3] Action Items:")
    for i, item in enumerate(extracted.action_items):
        print(f"  {i+1}. {item.action_title}")
        print(f"      Owner: {item.owner_name} | Due: {item.resolved_due_date}")
        print(f"      Confidence: {item.confidence_score}")
        print(f"      Quote: {item.quote_provenance[:80]}...")

    # Simulate approval
    approved = [
        {
            "action_title": item.action_title,
            "owner_name": item.owner_name,
            "resolved_due_date": item.resolved_due_date,
            "priority": item.priority,
            "quote_provenance": item.quote_provenance,
        }
        for item in extracted.action_items
    ]

    print("\n[4] Simulating human approval...")
    resume_state: AgentState = {
        "human_feedback": "approve",
        "approved_items": approved,
    }

    for event in graph.stream(resume_state, config, stream_mode="values"):
        pass

    snapshot = graph.get_state(config)
    results = snapshot.values.get("execution_results", [])

    print(f"\n[5] Execution Results ({len(results)} items):")
    for r in results:
        print(f"  {r}")

    print("\n✅ Pipeline test complete.")


if __name__ == "__main__":
    main()
