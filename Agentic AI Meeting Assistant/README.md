# TechBharat Buildathon — Agentic AI Meeting Assistant

> AI proposes meeting commitments with evidence. You approve each one. Then GitHub issues are created. Zero unapproved side effects.

## Quick start (demo)

```powershell
cd "Agentic AI Meeting Assistant"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # fill in keys (see BUILD_PLAN.md)
uvicorn main:app --reload
```

Open **http://localhost:8000/ui**

Follow the step-by-step demo script in **`DEMO.md`**.

## What the demo does

1. Paste or upload a meeting transcript (`.txt`, `.vtt`, `.srt`, or audio/video)
2. AI extracts summary, decisions, risks, and action items with quote evidence
3. You **approve or reject each item individually**
4. Dispatch creates GitHub issues (sandbox repo)
5. Optional Slack recap if `SLACK_WEBHOOK_URL` is set
6. Re-run → no duplicate issues (idempotent)

## Required `.env` for live demo

```text
GROQ_API_KEY=...
INSFORGE_URL=...
INSFORGE_API_KEY=...
DRY_RUN=false
GITHUB_TOKEN=...
GITHUB_REPO=owner/sandbox-repo
```

Optional: `SLACK_WEBHOOK_URL=...`

See **`BUILD_PLAN.md`** for setup checklist.

## Architecture

```
Ingest → Groq (STT if media) → LangGraph extract → resolve roster/dates
  → persist candidates → /ui review → dispatch → GitHub (+ Slack)
  → audit log in InsForge
```

Full product roadmap: **`PLAN.md`**

## API (main endpoints)

| Endpoint | Purpose |
|----------|---------|
| `POST /ingest` | Paste text transcript |
| `POST /ingest/file` | Upload `.txt` / `.vtt` / `.srt` |
| `POST /media/*` | Audio/video upload + transcribe |
| `POST /meetings/{id}/action-items/{id}/review` | Approve / reject item |
| `POST /meetings/{id}/dispatch` | Create approved GitHub issues |
| `POST /meetings/{id}/ask` | Q&A over transcript |
| `GET /meetings/{id}` | Audit log |
| `GET /ui` | Demo UI |

## Team roster

Edit `data/team_members.json` to map spoken names → GitHub logins. Used during owner resolution and pre-filled in the review UI.

## Tests & eval

```powershell
python -m pytest -q
python eval_gold.py   # needs GROQ_API_KEY
```

## Scope

**In scope now:** Individual mode, human review gate, GitHub dispatch, optional Slack recap, Q&A.

**Post-buildathon:** Organization mode, Jira, email, Google Meet auto-ingest. See `PLAN.md`.

## InsForge

Project backend: `https://cgjubsx4.ap-southeast.insforge.app`

Never commit `.env`, API keys, or service account files.
