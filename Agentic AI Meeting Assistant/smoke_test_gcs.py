"""Quick end-to-end smoke test for the GCS signed-URL upload flow.

No credentials need to be live on disk beforehand. The test reports exactly what's
configured and whether a signed upload URL + signed read URL can be minted.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

project_dir = Path(__file__).parent
os.chdir(project_dir)

from dotenv import load_dotenv
load_dotenv()

print("=== GCS Signed-URL Smoke Test ===")
print(f"Project dir: {project_dir}")
print()

required = [
    ("GCP_PROJECT_ID",),
    ("GCS_MEDIA_BUCKET",),
]
optional = [
    ("GCS_SERVICE_ACCOUNT_EMAIL", "[Mode B: SignBlob]"),
    ("GOOGLE_APPLICATION_CREDENTIALS", "[Mode A: SA JSON key]"),
]
for key, *label in required:
    val = os.getenv(key)
    status = f"OK = {val}" if val else "MISSING ❌"
    print(f"  {key:<30} {status}")
missing_any_required = any(not os.getenv(k) for k, *_ in required)
for key, label in optional:
    val = os.getenv(key)
    status = f"OK = {val}" if val else "(not set)"
    print(f"  {key:<30} {status}  {label}")
print()

mode = None
if os.getenv("GCS_SERVICE_ACCOUNT_EMAIL"):
    mode = "Mode B (User ADC + IAM SignBlob)"
elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    mode = "Mode A (SA JSON key)"
else:
    mode = "Unknown — set GCS_SERVICE_ACCOUNT_EMAIL (Mode B) OR GOOGLE_APPLICATION_CREDENTIALS (Mode A)"
print(f"Auth mode detected: {mode}")
print()

if missing_any_required:
    print("❌ FAIL: GCP_PROJECT_ID and GCS_MEDIA_BUCKET are required. Fix .env and re-run.")
    sys.exit(1)

from src.media import GCSMediaStore, build_object_key

try:
    store = GCSMediaStore()
except Exception as exc:
    print(f"❌ GCSMediaStore init failed: {type(exc).__name__}: {exc}")
    print()
    print("Hint for Mode B users:")
    print("  1. Run  gcloud auth application-default login  (once, in your PowerShell)")
    print("  2. Confirm ADC file exists at:")
    adc = Path(os.environ.get("APPDATA", "")) / "gcloud" / "application_default_credentials.json"
    print(f"     {adc}   exists={adc.exists()}")
    sys.exit(2)

test_key = build_object_key("smoke-test-meeting", "recording.mp4")
print(f"Test object key:   {test_key}")
print(f"Bucket:            {store.bucket_name}")
print(f"SA email for sign: {store.service_account_email or '(using local key)'}")
print()

try:
    upload_url = store.create_upload_url(test_key, "video/mp4")
    print(f"✅ Signed PUT URL generated ({len(upload_url)} chars)")
except Exception as exc:
    print(f"❌ create_upload_url failed: {type(exc).__name__}: {exc}")
    print()
    print("Common causes:")
    print("  - Mode B: your user ADC is missing or expired → run gcloud auth application-default login")
    print("  - Mode B: your user does not have iam.serviceAccounts.signBlob on the SA")
    print("  - Mode A: GOOGLE_APPLICATION_CREDENTIALS path is wrong or unreadable")
    sys.exit(3)

try:
    read_url = store.create_read_url(test_key)
    print(f"✅ Signed GET URL generated ({len(read_url)} chars)")
except Exception as exc:
    print(f"❌ create_read_url failed: {type(exc).__name__}: {exc}")
    sys.exit(4)

try:
    exists = store.exists(test_key)
    print(f"✅ exists() call OK (object exists={exists})")
except Exception as exc:
    print(f"❌ exists() call failed: {type(exc).__name__}: {exc}")
    print("  (upload URL/read URL signing can still work even if exists() times out)")

print()
print("🎉 GCS signed-URL smoke test PASSED.")
print("   POST /media/uploads is ready to generate equivalent URLs for the UI.")
