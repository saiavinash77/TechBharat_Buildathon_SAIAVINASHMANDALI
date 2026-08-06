# Build Plan — Buildathon Demo (<24 hours)

> **Strategy:** Ship one bulletproof Individual demo. No Jira. Slack optional. Org mode on slides only.

---

## Demo target (what judges see live)

```
Open /ui → paste transcript → see summary + tasks + evidence
→ reject 1 item → approve 2 items → Dispatch → GitHub issues appear
→ re-run same file → already_dispatched (no duplicates) → show audit log
```

**Optional if you add webhook:** Slack recap posts after dispatch.

**Not in live demo:** Jira, email, Google Meet, org dashboard, Chainlit.

---

## Build tasks (in order)

| # | Task | Status |
|---|------|--------|
| 1 | Pre-fill GitHub assignee from team roster in review UI | ✅ |
| 2 | Add Q&A panel to `/ui` (ask about loaded meeting) | ✅ |
| 3 | Polish dispatch results + audit display + dry-run banner | ✅ |
| 4 | Update README + `.env.example` for demo setup | ✅ |
| 5 | Add `POST /meetings/{id}/ask` API for Q&A | ✅ |
| 6 | Run tests — all green | ✅ |

## Skipped (post-buildathon)

- Jira adapter
- Email assignees
- Org / teams / auth
- Google Meet sync
- Next.js frontend
- Chainlit fixes (deprecated for demo)

---

## What YOU must provide (nothing else needed)

Copy into `.env` — **do not commit**:

```text
# Required
GROQ_API_KEY=gsk_...
INSFORGE_URL=https://cgjubsx4.ap-southeast.insforge.app
INSFORGE_API_KEY=...

# Live GitHub dispatch (required for demo)
DRY_RUN=false
GITHUB_TOKEN=ghp_... or github_pat_...
GITHUB_REPO=your-username/your-sandbox-repo

# Optional — Slack recap after dispatch
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### GitHub sandbox setup (5 min)
1. Create empty repo e.g. `buildathon-meeting-tasks`
2. Settings → Developer settings → Fine-grained token
3. Scope: Issues read/write on that repo only
4. Set `GITHUB_REPO=owner/repo` and `DRY_RUN=false`

### Slack setup (optional, 10 min)
1. https://api.slack.com/apps → Create app → Incoming Webhooks
2. Add webhook to `#general` or `#demo`
3. Paste URL as `SLACK_WEBHOOK_URL`

**I will ask you only when blocked on these values.**

---

## Success checklist (before you present)

- [ ] `python -m pytest -q` → all pass
- [ ] `uvicorn main:app --reload` → `/ui` loads
- [ ] Paste `data/sample_transcript.txt` → items appear
- [ ] Approve 2 → Dispatch → issues in GitHub repo
- [ ] Dispatch again → `already_dispatched`
- [ ] Audit log shows events at bottom of `/ui`
- [ ] Practiced `DEMO.md` once end-to-end

---

## After buildathon (Phase 1 backlog)

1. Jira adapter (sandbox)
2. Email via InsForge
3. Org + teams in InsForge
4. Next.js org dashboard

See `PLAN.md` for full product roadmap.
