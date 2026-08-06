# Demo script — 5 minutes (Use Case B)

## Before demo
1. `DRY_RUN=false` in `.env` with sandbox `GITHUB_TOKEN` + `GITHUB_REPO`
2. `uvicorn main:app --reload` then open **http://localhost:8000/ui**
3. Have `data/sample_transcript.txt` ready as backup

## Narrative (follow in order)

### 1. Problem (30s)
> Meetings lose commitments. Transcripts capture words, not accountability. Our agent extracts commitments, a human approves each one, then creates GitHub issues — never the other way around.

### 2. Ingest (45s)
- Tab **Paste transcript** → paste a messy 10–15 line standup (or upload `.vtt`)
- Click **Analyze**
- Point out: executive summary, decisions, open questions, **risks/blockers**, action items with **quote evidence**

### 3. Human review (90s) — THIS WINS POINTS
- **Reject** one weak/discussion item
- **Edit** one owner or due date on an explicit commitment
- **Approve** 2–3 eligible items (green/yellow badges only)
- Say: *"Nothing hits GitHub until I approve each item individually."*

### 4. Dispatch (45s)
- Click **Dispatch approved to GitHub**
- Open sandbox repo — issues appeared with labels `meeting-assistant`, `explicit-commitment` or `needs-confirmation`
- If `SLACK_WEBHOOK_URL` is set, recap posts to Slack automatically
- Show **audit log** at bottom — EXTRACTION_COMPLETED, REVIEW_APPROVED, GITHUB_ISSUE_DISPATCHED

### 5. Idempotency (30s)
- Re-upload **same transcript**
- Approve same items → Dispatch again
- Show status **already_dispatched** — zero duplicates

### 6. Safety close (30s)
> Discussion-only items are blocked. Unapproved items never dispatch. Every action is auditable.

## Fallbacks
| Failure | Fallback |
|---------|----------|
| GCS upload fails | Use **Paste transcript** tab |
| Groq down | Pre-run extraction; show review UI with cached meeting via GET `/meetings/{id}` |
| GitHub fails | `DRY_RUN=true` — explain dry-run policy, show audit trail |

## Judge metrics we hit
- Action item recall/precision → run `python eval_gold.py`
- Owner accuracy → roster in `data/team_members.json`
- Zero unapproved actions → per-item review gate
- Duplicate suppression → idempotent dispatch
- Under 3 min E2E → text ingest path (no STT wait)
