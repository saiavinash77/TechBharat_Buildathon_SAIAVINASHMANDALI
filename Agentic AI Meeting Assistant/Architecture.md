# Architecture — Buildathon demo (Use Case B)

## Goal
Turn meeting evidence into **reviewer-approved GitHub issues**. AI proposes; humans approve; agent dispatches. Zero unapproved side effects.

## Single pipeline (everything flows here)

```
Ingest (text | .vtt/.srt | audio/video)
    → Groq Whisper (media only)
    → LangGraph: extract → resolve (dates + roster) → REVIEW INTERRUPT
    → InsForge: persist candidates + audit
    → UI: per-item APPROVE / REJECT / EDIT
    → POST /dispatch → GitHub Issues (sandbox)
    → InsForge: dispatch_attempts + audit_events (idempotent)
```

## Components

| Piece | Role |
|-------|------|
| `main.py` + `/ui` | Demo surface — **only UI judges need** |
| `src/graph.py` | LangGraph agent workflow |
| `src/ingest_workflow.py` | Unified text ingest → durable candidates |
| `src/durable_workflow.py` | Per-item review + idempotent GitHub dispatch |
| `src/roster.py` | Owner → email + GitHub login |
| `src/transcript_parser.py` | .txt / .vtt / .srt |
| InsForge | Meetings, action items, audit log, dispatch attempts |
| GCS + Groq | Optional media path (stretch depth) |

## Accountability classes
- **EXPLICIT_COMMITMENT** → may assign GitHub user after review
- **NEEDS_CONFIRMATION** → unassigned issue + `needs-confirmation` label
- **DISCUSSION_ONLY** → blocked from GitHub

## Deferred (not for 15hr demo)
- Next.js frontend
- Cross-meeting RAG / memory
- Slack/Jira/Linear integrations
- Live meeting mode
- Chainlit (dev-only; demo uses `/ui`)

## Run
```powershell
uvicorn main:app --reload
# Demo: http://localhost:8000/ui
# Eval:  python eval_gold.py
```
