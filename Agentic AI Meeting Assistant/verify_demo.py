#!/usr/bin/env python3
"""Pre-demo checklist — verifies .env without printing secrets."""

from __future__ import annotations

import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

REPO = os.getenv("GITHUB_REPO", "saiavinash77/TechBharat_Buildathon_SAIAVINASHMANDALI")
ISSUES_URL = f"https://github.com/{REPO}/issues"


def _set(name: str) -> bool:
    return bool(os.getenv(name, "").strip())


def main() -> int:
    print("=" * 60)
    print("BUILDATHON DEMO — CONFIG CHECK")
    print("=" * 60)

    checks: list[tuple[str, bool, str]] = [
        ("GROQ_API_KEY", _set("GROQ_API_KEY"), "Required for extraction"),
        ("INSFORGE_URL", _set("INSFORGE_URL"), "Required for review + audit"),
        ("INSFORGE_API_KEY", _set("INSFORGE_API_KEY"), "Required for review + audit"),
        ("GITHUB_TOKEN", _set("GITHUB_TOKEN"), "Required for live issue creation"),
        ("GITHUB_REPO", _set("GITHUB_REPO"), f"Should be: saiavinash77/TechBharat_Buildathon_SAIAVINASHMANDALI"),
        ("DRY_RUN=false", os.getenv("DRY_RUN", "true").lower() == "false", "Set DRY_RUN=false for live demo"),
        ("SLACK_WEBHOOK_URL", _set("SLACK_WEBHOOK_URL"), "Optional — Slack recap after dispatch"),
    ]

    failed = 0
    for name, ok, hint in checks:
        icon = "OK" if ok else "MISSING"
        print(f"  [{icon:7}] {name}")
        if not ok and name != "SLACK_WEBHOOK_URL":
            print(f"           -> {hint}")
            failed += 1
        elif not ok:
            print(f"           -> {hint} (optional)")

    print()
    print(f"  Issues will appear at: {ISSUES_URL}")
    print()

    token = os.getenv("GITHUB_TOKEN", "")
    repo = os.getenv("GITHUB_REPO", REPO)
    if token and repo:
        print("  Testing GitHub API access...")
        resp = requests.get(
            f"https://api.github.com/repos/{repo}",
            headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"},
            timeout=10,
        )
        if resp.status_code == 200:
            print(f"  [OK     ] GitHub repo reachable: {repo}")
            perms = resp.json().get("permissions", {})
            if perms.get("push") or perms.get("admin"):
                print("  [OK     ] Token has write access")
            else:
                print("  [WARN   ] Token may lack issue-create permission — test with a live dispatch")
        else:
            print(f"  [FAIL   ] GitHub API {resp.status_code} — check token and repo name")
            failed += 1

    if _set("SLACK_WEBHOOK_URL"):
        print("  [OK     ] Slack webhook configured (not pinged — avoids spam)")

    print()
    if failed:
        print(f"Fix {failed} required item(s) above, then run: uvicorn main:app --reload")
        print("Full steps: DEMO_SETUP.md")
        return 1

    print("All required checks passed. Start server:")
    print("  uvicorn main:app --reload")
    print("  Open http://localhost:8000/ui")
    return 0


if __name__ == "__main__":
    sys.exit(main())
