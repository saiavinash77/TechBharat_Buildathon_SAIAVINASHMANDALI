#!/usr/bin/env python3
"""Quick extraction quality check against labeled sample (no GitHub/InsForge required)."""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from src.nodes.extract import extract_node
from src.nodes.resolve import resolve_node


GOLD_PATH = Path("data/gold_labels.json")


def normalize(s: str) -> str:
    return " ".join(s.lower().split())


def main() -> int:
    if not os.getenv("GROQ_API_KEY"):
        print("Set GROQ_API_KEY to run live extraction eval.")
        return 1

    gold = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    transcript = Path(gold["transcript_file"]).read_text(encoding="utf-8")
    meeting_date = gold["meeting_date"]

    print("Running extraction against gold labels...")
    extracted = extract_node(transcript, meeting_date)
    resolved = resolve_node(extracted, meeting_date)

    found_titles = [normalize(i.action_title) for i in resolved.action_items]
    gold_items = gold["action_items"]

    matched = 0
    for g in gold_items:
        gnorm = normalize(g["title"])
        if any(gnorm in f or f in gnorm for f in found_titles):
            matched += 1
            print(f"  ✓ recall: {g['title']}")
        else:
            print(f"  ✗ miss:   {g['title']}")

    recall = matched / len(gold_items) if gold_items else 0
    precision = matched / len(resolved.action_items) if resolved.action_items else 0

    print(f"\nRecall:    {recall:.0%} ({matched}/{len(gold_items)})")
    print(f"Precision: {precision:.0%} (matched/{len(resolved.action_items)} extracted)")
    print(f"Target:    80% recall, 75% precision")
    return 0 if recall >= 0.8 else 2


if __name__ == "__main__":
    sys.exit(main())
