# TechBharat Buildathon — Agentic AI Meeting Assistant

> A safety-first workflow that turns meeting evidence into reviewer-approved GitHub issues. AI proposes tasks; it never creates accountability by itself.

## Architecture

![Safety-first meeting assistant architecture](docs/architecture.svg)

## What lives where

| Service | Responsibility |
|---|---|
| GCP Cloud Storage | Private raw audio/video objects and short-lived signed upload URLs. |
| Groq | Speech-to-text with timestamp evidence, plus structured extraction and current-meeting Q&A. |
| LangGraph | Agent workflow: extract, validate, native reviewer interrupt, and resume. |
| InsForge | Media metadata, transcript segments, action items, reviews, workflow state, and audit records. |
| GitHub | The destination for only reviewer-approved eligible issues. |

## Accountability policy

| Classification | GitHub outcome |
|---|---|
| `EXPLICIT_COMMITMENT` | The speaker directly accepted the work. After review, an issue may be assigned only when a verified GitHub login is supplied. |
| `NEEDS_CONFIRMATION` | A request or unclear ownership. After review, create an unassigned issue with `needs-confirmation`. |
| `DISCUSSION_ONLY` | An idea, question, or discussion. It is blocked from GitHub. |

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
Copy-Item .env.example .env
uvicorn main:app --reload
```

For the Chainlit UI:

```powershell
chainlit run app.py
```

Configure `.env` with server-only credentials. Do not commit it.

```text
INSFORGE_URL=https://...
INSFORGE_API_KEY=...
GROQ_API_KEY=...
GCP_PROJECT_ID=...
GCS_MEDIA_BUCKET=...
GOOGLE_APPLICATION_CREDENTIALS=C:\path\service-account.json
DRY_RUN=true
```

## Media flow

The UI accepts supported media files up to 100 MB. The API supports signed uploads up to the configurable 500 MB limit:

1. `POST /media/uploads` with title, meeting date, filename, MIME type, and byte size.
2. Upload bytes to the returned GCS `upload_url` via `PUT`, using the returned `Content-Type` header.
3. `POST /media/{media_id}/confirm-upload`.
4. `POST /media/{media_id}/transcribe`.
5. Review each persisted candidate with `POST /meetings/{meeting_id}/action-items/{action_item_id}/review`.
6. When ready, explicitly call `POST /meetings/{meeting_id}/dispatch`.

The fourth call transcribes the private object, records timestamped segments and extracted candidates in InsForge, then enters the LangGraph review gate. The review endpoint records the original AI proposal and reviewer decision before dispatch is possible. Raw media remains private in GCS; InsForge stores only the object key and durable workflow data.

## Scope

Included now: transcript input, private audio/video uploads, transcription, timestamp evidence, strict commitment classification, reviewer interrupt, current-meeting Q&A, safe GitHub dispatch, and InsForge workflow tables.

Deferred: cross-meeting RAG, Slack/Jira/Linear/email integrations, automatic speaker identity, and video-vision analysis.

## InsForge

The linked InsForge project holds durable application records. Use its CLI through:

```powershell
npx -y @insforge/cli current
```

Never commit `.insforge/project.json`, API keys, service-account files, or other credentials.
