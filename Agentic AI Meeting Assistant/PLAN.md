# Product Plan — Agentic AI Meeting Assistant

> **Vision:** Two modes sharing one agent core — **Individual** (upload & ask) and **Organization** (teams, auto-ingest, assign tasks, notify via Slack/Jira/email).

**Last updated:** Buildathon phase — post-demo roadmap included.

---

## 1. Where we are today (baseline)

### ✅ Built and working
| Component | Status | Location |
|-----------|--------|----------|
| Agent pipeline (extract → resolve → review → dispatch) | Done | `src/graph.py`, `src/ingest_workflow.py` |
| Human-in-the-loop review (per item) | Done | `/ui`, `src/durable_workflow.py` |
| Text + VTT/SRT ingest | Done | `POST /ingest`, `POST /ingest/file` |
| Audio/video → GCS → Groq Whisper | Done | `src/media_workflow.py` |
| GitHub Issues dispatch (idempotent) | Done | `src/nodes/execute.py` |
| Slack recap (webhook, post-dispatch) | Partial | `src/slack_recap.py` — needs webhook URL |
| Team roster (name → email → GitHub) | Done (file) | `data/team_members.json`, `src/roster.py` |
| Audit log | Done | InsForge `audit_events` |
| Demo UI | Done | `templates/ui.html` → `/ui` |
| Eval script | Done | `eval_gold.py` |
| Tests | 19/19 passing | `tests/` |

### ⚠️ Exists but not demo-ready
| Component | Issue |
|-----------|-------|
| Chainlit (`app.py`) | Legacy bulk-approve path — **do not use for demo** |
| Next.js frontend | Scaffold only — not connected to API |
| README / Architecture | Slightly outdated vs code |
| Roster → UI | GitHub login not auto-filled from roster |
| Q&A on meeting | Works in Chainlit, not in `/ui` |

### ❌ Not built yet
| Component | Needed for |
|-----------|------------|
| User auth + orgs/teams | Organization mode |
| Jira integration | Org task dispatch |
| Email notifications | Assignee alerts |
| Google Meet / Calendar / Drive sync | Auto-ingest org meetings |
| Org dashboard | Team lead review at scale |
| Daily digest | "What happened today" |
| Cross-meeting memory | Recurring standups |

---

## 2. Product modes (target state)

### Mode A — Individual
**Who:** Solo user, freelancer, student, anyone with a recording.

```
Upload (audio / video / text / vtt)
  → Transcribe (if media)
  → AI: summary, decisions, risks, action items + quotes
  → User asks Q&A about the meeting
  → Optional: approve items → push to personal GitHub / export
```

**Success criteria:**
- End-to-end in under 3 minutes (text path)
- No account required for MVP
- Q&A works in same UI as review

---

### Mode B — Organization
**Who:** Company team with recurring Google Meet / standups.

```
Admin creates Org → Teams → Members (roster)
  → Connect integrations (Slack workspace, Jira project, Google Workspace)
  → Meeting ends (manual upload today; GMeet/Drive later)
  → Agent extracts tasks, maps owners via org roster
  → Team lead reviews in dashboard
  → Dispatch: Jira tickets + Slack recap + email to assignees
  → Daily digest: today's meetings, decisions, open tasks
```

**Success criteria:**
- Zero unapproved external actions (same safety gate)
- Owner resolved to real email / Jira account / Slack mention
- One team can run 5 meetings/week without duplicate tasks

---

## 3. Shared agent core (both modes use this)

```
┌─────────────────────────────────────────────────────────┐
│                    SHARED AGENT CORE                     │
├─────────────────────────────────────────────────────────┤
│ Ingest → Transcribe → Extract → Resolve → Review Gate │
│                              ↓                           │
│                    Dispatch Adapters                     │
│         GitHub │ Jira │ Slack │ Email │ (future)        │
│                              ↓                           │
│                    Audit Log (InsForge)                  │
└─────────────────────────────────────────────────────────┘
```

**Non-negotiable rules (buildathon + product):**
1. AI proposes — never auto-assigns accountability
2. Human approves each item individually
3. Idempotent dispatch (re-run = no duplicates)
4. Full audit trail (who approved what, when, based on which quote)

---

## 4. Integration plan

### Priority matrix

| Integration | Buildathon demo | Phase 1 (1–2 weeks) | Phase 2 (3–4 weeks) |
|-------------|-----------------|---------------------|---------------------|
| **GitHub Issues** | ✅ Live sandbox | Production tokens per org | — |
| **Slack** | Webhook recap | Channel recap + @mentions | Workspace app |
| **Jira** | — | Create issues in sandbox project | Assignee mapping |
| **Email** | — | InsForge email to assignees | Digest emails |
| **Google Meet** | — | — | Calendar + Drive sync |

---

### 4.1 GitHub (done — tune for demo)
- **Status:** Implemented
- **Needs:** `DRY_RUN=false`, sandbox `GITHUB_TOKEN`, `GITHUB_REPO`
- **Phase 1:** Per-org repo config in DB instead of `.env`

---

### 4.2 Slack
- **Status:** Webhook recap after dispatch (`src/slack_recap.py`)
- **Phase 1 targets:**
  - [ ] Post recap to `#team-meetings` with meeting title + approved items + links
  - [ ] @mention assignee when Slack user ID mapped in roster
  - [ ] Audit event `SLACK_RECAP_POSTED`
- **Phase 2:** Slack App (OAuth), slash command `/meeting-upload`, interactive approve buttons
- **Needs from you:** Slack Incoming Webhook URL (Phase 1) or Slack App credentials (Phase 2)

---

### 4.3 Jira
- **Status:** Not built
- **Phase 1 targets:**
  - [ ] `src/adapters/jira.py` — create issue in sandbox project
  - [ ] Map owner → Jira accountId via org roster
  - [ ] Labels: `meeting-assistant`, classification, priority
  - [ ] Description: quote provenance + meeting link
  - [ ] Idempotency key stored in InsForge (same pattern as GitHub)
  - [ ] Dispatch config: `DISPATCH_TARGETS=github,jira,slack` per org
- **Phase 2:** Bi-directional sync (mark done when Jira ticket closed)
- **Needs from you:** Jira Cloud site URL, API token, sandbox project key (e.g. `DEMO`)

---

### 4.4 Email
- **Status:** Not built
- **Phase 1 targets:**
  - [ ] After approved dispatch → email assignee: task title, due date, quote, link to Jira/GitHub
  - [ ] Use InsForge email API (server-side)
  - [ ] Only send after human approval (never on extraction alone)
- **Phase 2:** Daily digest to team lead at 6pm
- **Needs from you:** Confirm sender domain / InsForge email setup

---

### 4.5 Google Meet (Phase 2 — not buildathon)
- **Approach:** Calendar API (scheduled meetings + attendees) + Drive API (recordings + auto-transcripts)
- **Flow:** Meeting ends → new file in `Meet Recordings` folder → webhook/poll → run pipeline → tag to team by attendee domain
- **Needs from you:** Google Workspace test account + OAuth consent

---

## 5. Execution phases — clear targets

### Phase 0 — Buildathon demo (NOW → demo day)
**Goal:** Win Use Case B with Individual mode on `/ui`.

| # | Task | Owner | Done? |
|---|------|-------|-------|
| 0.1 | Set `DRY_RUN=false` + sandbox GitHub | You | ☐ |
| 0.2 | Practice `DEMO.md` script 2× on `/ui` | You | ☐ |
| 0.3 | Run `python eval_gold.py` — target 80% recall | You | ☐ |
| 0.4 | Optional: set `SLACK_WEBHOOK_URL` for live recap | You | ☐ |
| 0.5 | Update README to match `/ui` workflow | Dev | ☐ |

**Demo narrative:** Individual upload → review → GitHub → idempotency → pitch Org mode as roadmap.

---

### Phase 1 — Individual polish + Slack/Jira (Week 1)
**Goal:** One person can upload, Q&A, and dispatch to GitHub **or** Jira + Slack recap.

| # | Task | Target |
|---|------|--------|
| 1.1 | Add Q&A panel to `/ui` | Ask questions about loaded transcript |
| 1.2 | Pre-fill GitHub/Jira assignee from roster | Less manual typing in review |
| 1.3 | Jira adapter + sandbox dispatch | Create Jira issue on approve |
| 1.4 | Slack webhook polish | Formatted recap with links |
| 1.5 | `DISPATCH_TARGETS` env config | `github`, `jira`, `slack` (comma-separated) |
| 1.6 | Fix/remove Chainlit legacy path | Single pipeline only |
| 1.7 | Update tests for Jira adapter | Mock Jira API |

**Exit criteria:** Upload transcript → approve 2 items → see GitHub issue + Jira ticket + Slack message.

---

### Phase 2 — Organization foundation (Week 2–3)
**Goal:** Multi-tenant org with teams, roster in DB, team lead dashboard.

| # | Task | Target |
|---|------|--------|
| 2.1 | InsForge schema: `organizations`, `teams`, `team_members` | Replace JSON roster |
| 2.2 | InsForge Auth: signup, login, org invite | User accounts |
| 2.3 | Row-level security: users see only their org | Security |
| 2.4 | API: CRUD org/team/members | Backend |
| 2.5 | Next.js dashboard: org home, today's meetings, pending reviews | `frontend/` |
| 2.6 | Per-org integration settings (GitHub repo, Jira project, Slack webhook) | Settings page |
| 2.7 | Email assignee on dispatch | InsForge email |

**Exit criteria:** Admin creates org → adds team + members → member uploads meeting → lead approves → Jira + Slack + email fire.

---

### Phase 3 — Auto-ingest + digest (Week 4+)
**Goal:** Organization mode feels automatic.

| # | Task | Target |
|---|------|--------|
| 3.1 | Google Calendar OAuth — list today's meetings | Calendar view |
| 3.2 | Google Drive watch — new Meet recording | Auto pipeline trigger |
| 3.3 | Daily digest job (InsForge schedule) | Email/Slack summary |
| 3.4 | Cross-meeting memory | Carry forward open items |
| 3.5 | Evidence timestamp links | Click quote → jump to transcript moment |

**Exit criteria:** Meeting ends → recording auto-processed → team lead gets digest → approves → tasks assigned.

---

## 6. Data model (Organization — Phase 2)

```
organizations
  id, name, slug, created_at

teams
  id, org_id, name

team_members
  id, team_id, display_name, email,
  github_login, jira_account_id, slack_user_id, aliases[]

org_integrations
  id, org_id,
  github_repo, jira_site, jira_project_key,
  slack_webhook_url, dispatch_targets[]

meetings (extend existing)
  + org_id, team_id, created_by_user_id, source

action_items (extend existing)
  + org_id, jira_issue_key, slack_message_ts
```

---

## 7. Tech stack (confirmed)

| Layer | Choice | Why |
|-------|--------|-----|
| Agent | LangGraph | Review interrupt, re-extraction |
| LLM + STT | Groq | Speed for demo latency |
| Backend | FastAPI | Current API |
| Database + Auth + Email | InsForge | Already integrated |
| Media storage | GCS | Private uploads |
| Demo UI | `/ui` (HTML) | Reliable for judges |
| Org dashboard | Next.js (`frontend/`) | Phase 2 |
| Dispatch | Adapter pattern | GitHub, Jira, Slack, Email |

---

## 8. What I need from you (decisions + credentials)

Answer these so implementation can start without guessing:

### A. Timeline
1. **When is the buildathon demo?** (hours / days left)
2. **After demo, how many weeks for Phase 1?**

### B. Integrations priority (pick order)
Rank 1–4: GitHub, Jira, Slack, Email

### C. Credentials (sandbox only — never commit)
| Service | What to provide |
|---------|-----------------|
| GitHub | Sandbox repo + fine-grained token (issues write) |
| Jira Cloud | Site URL (e.g. `yourteam.atlassian.net`), email, API token, project key |
| Slack | Incoming webhook URL **or** Slack App bot token + channel ID |
| Email | Confirm if InsForge email is enabled on your project |
| Google (Phase 3) | Workspace test account — yes/no |

### D. Organization
1. **Org name for demo** (e.g. "TechBharat Demo Corp")
2. **Team names** (e.g. Engineering, Product)
3. **Real member list** for roster (name, email, GitHub, Jira email, Slack handle) — 3–5 people enough

### E. Product decisions
1. **Demo Mode A only**, or try to show Mode B mock in slides?
2. **Jira vs GitHub** — which is primary dispatch for your org story?
3. **Auth required** for Individual mode, or stay open upload?

---

## 9. Recommended immediate next steps

**If demo is within 24–48 hours:**
1. You: GitHub sandbox credentials + practice demo
2. Dev: README update + optional Slack webhook test
3. **Do not** start Jira/GMeet until after demo

**If demo is 1+ week away:**
1. Phase 0 (demo polish)
2. Phase 1.3–1.5 (Jira + Slack adapters)
3. Show dual dispatch in demo (strong differentiator)

---

## 10. One-line pitch (both modes)

> **Individual:** Upload any meeting — AI extracts commitments with evidence; you approve; tasks land in GitHub or Jira.  
> **Organization:** Teams connect Meet + Slack + Jira — every sync becomes assigned, auditable work with zero unapproved actions.

---

*Next action: Answer Section 8 → we start Phase 0 or Phase 1 based on your timeline.*
