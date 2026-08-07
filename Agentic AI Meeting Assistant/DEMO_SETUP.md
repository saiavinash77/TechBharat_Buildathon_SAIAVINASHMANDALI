# Demo setup — Option A (<24 hours)

**Repo:** [TechBharat_Buildathon_SAIAVINASHMANDALI](https://github.com/saiavinash77/TechBharat_Buildathon_SAIAVINASHMANDALI/tree/buildathon-v1/Agentic%20AI%20Meeting%20Assistant)

**Issues tab (live proof):** https://github.com/saiavinash77/TechBharat_Buildathon_SAIAVINASHMANDALI/issues

---

## Step 1 — Copy env file

```powershell
cd "Agentic AI Meeting Assistant"
Copy-Item .env.example .env
```

Edit `.env` — fill only what you have; never commit `.env`.

---

## Step 2 — GitHub token (required for live demo)

1. Open https://github.com/settings/tokens?type=beta (Fine-grained token)
2. **Repository access:** Only `TechBharat_Buildathon_SAIAVINASHMANDALI`
3. **Permissions → Issues:** Read and write
4. Generate and copy token into `.env`:

```text
GITHUB_TOKEN=github_pat_xxxxxxxx
GITHUB_REPO=saiavinash77/TechBharat_Buildathon_SAIAVINASHMANDALI
DRY_RUN=false
```

> Issues will be created in your buildathon repo so judges can refresh the Issues page and see them appear.

---

## Step 3 — Slack webhook (optional, ~15 min)

1. Go to https://api.slack.com/apps → Create New App → From scratch
2. **Incoming Webhooks** → Activate → Add New Webhook to Workspace
3. Pick a channel (e.g. `#general` or create `#meeting-recap`)
4. Copy webhook URL into `.env`:

```text
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T000/B000/XXXX
```

---

## Step 4 — Verify config

```powershell
python verify_demo.py
```

All required checks should show `OK`.

---

## Step 5 — Run server

```powershell
uvicorn main:app --reload
```

Open **http://localhost:8000/ui**

---

## Step 6 — 3-minute dry run

1. Paste contents of `data/sample_transcript.txt` → **Analyze**
2. **Reject** one discussion-only item
3. **Approve** 2 items (set GitHub assignee `saiavinash77` on explicit commitment if you want)
4. **Dispatch approved to GitHub**
5. Open https://github.com/saiavinash77/TechBharat_Buildathon_SAIAVINASHMANDALI/issues — issues should appear
6. Check Slack channel if webhook configured
7. Re-analyze same text → approve → dispatch → status **already_dispatched**

Full judge script: **DEMO.md**

---

## Fallback if GitHub fails live

Set `DRY_RUN=true`, show audit log in UI, say:

> *"Safety policy defaults to dry-run; flip one env flag for production dispatch."*

---

## What you do NOT need for demo

- Jira (Phase 1 after buildathon)
- Google Meet API
- Next.js frontend
- Chainlit (`chainlit run app.py`) — use `/ui` only
