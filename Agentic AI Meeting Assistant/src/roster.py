"""Team roster: map spoken names to email + GitHub login for owner resolution."""

from __future__ import annotations

import json
import os
from pathlib import Path


def load_roster(path: str | None = None) -> dict[str, dict]:
    """Return canonical_name -> {email, github, aliases}."""
    roster_path = Path(path or os.getenv("TEAM_ROSTER_PATH", "data/team_members.json"))
    if not roster_path.exists():
        return {}
    try:
        raw = json.loads(roster_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    roster: dict[str, dict] = {}
    for canonical, info in raw.items():
        if not isinstance(info, dict):
            continue
        roster[canonical.title()] = {
            "email": info.get("email", ""),
            "github": info.get("github", canonical),
            "aliases": [a.lower() for a in info.get("aliases", [canonical])],
        }
    return roster


def resolve_owner(owner_name: str, roster: dict[str, dict] | None = None) -> dict:
    """Match owner_name against roster aliases. Returns resolution metadata."""
    roster = roster if roster is not None else load_roster()
    normalized = (owner_name or "").strip().lower()
    if not normalized or normalized == "unassigned":
        return {
            "owner_name": "Unassigned",
            "owner_resolution_status": "UNASSIGNED",
            "owner_email": None,
            "github_login": None,
        }

    for canonical, info in roster.items():
        aliases = info.get("aliases", [])
        if normalized in aliases or any(normalized in alias or alias in normalized for alias in aliases):
            return {
                "owner_name": canonical,
                "owner_resolution_status": "RESOLVED",
                "owner_email": info.get("email"),
                "github_login": info.get("github"),
            }

    return {
        "owner_name": owner_name.strip(),
        "owner_resolution_status": "UNRESOLVED",
        "owner_email": None,
        "github_login": None,
    }
