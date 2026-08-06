Demo quickstart

Preconditions
- Ensure the server is running: uvicorn main:app --host 127.0.0.1 --port 8000
- Ensure .env contains a valid GITHUB_TOKEN and (optionally) GITHUB_REPO for live dispatch.

Quick demo run (local demo data seeded)
1. Start server
   python -m uvicorn main:app --host 127.0.0.1 --port 8000

2. Run the demo script (from repo root):
   python demo_run.py

What the script does
- Creates a demo invite and joins a new user (upsert)
- Lists org members
- Lists action items for meeting "live-test-meeting-1" (seeded in files/)
- Triggers dispatch for that meeting and prints result (includes GitHub issue URL when created)

Environment variables
- GITHUB_TOKEN: Personal access token with repo (or Issues read/write) scope. For org repos, ensure token is allowed for the target repo.
- GITHUB_REPO: owner/repo or GitHub URL (optional; when missing, dispatch will use local fallback)
- USE_INSFORGE: set to 1 to use InsForgeRepository instead of local file fallback (not required for demo)

Notes
- Dispatch includes idempotency: re-running dispatch will not create duplicate GitHub issues for items already dispatched.
- If dispatch fails with a 422 (Validation Failed), check that any provided github_assignee_login is a valid collaborator for the target repo; remove or correct the assignee to proceed.
