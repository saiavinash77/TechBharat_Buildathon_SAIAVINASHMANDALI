# Backend Architecture Documentation

## Overview
The backend uses FastAPI with a multi-stage pipeline for processing meeting recordings:
1. **Media Upload** → GCS Storage
2. **Transcription** → Groq Whisper API
3. **AI Extraction** → LangGraph workflow
4. **Human Review** → InsForge persistence
5. **GitHub Dispatch** → Issue creation

## Video Storage Architecture

### GCS (Google Cloud Storage) Integration

**Storage Flow:**
1. **Frontend Upload**: User uploads video via `/media/direct-upload` endpoint
2. **GCS Storage**: Video stored in private GCS bucket using `GCSMediaStore`
3. **Signed URLs**: Temporary signed URLs for upload/read (15 min TTL by default)
4. **Fallback**: Local temp storage if GCS fails

**Key Components:**
- `src/media.py`: GCSMediaStore class handles all GCS operations
- `src/media_workflow.py`: Orchestrates upload → transcription → extraction
- `main.py`: FastAPI endpoints for media processing

**Authentication Modes:**
- **Mode A**: Service Account JSON key (traditional)
- **Mode B**: User ADC + IAM SignBlob (recommended, org-policy-safe)

**Storage Timing:**
- **Upload**: Direct GCS upload via signed URL (varies by file size)
- **Transcription**: Groq Whisper API (typically 1-3 min for 30 min video)
- **Extraction**: LangGraph workflow (30-60 seconds)
- **Total Time**: ~2-5 minutes for typical meeting recording

### GCS Storage Details

**File Structure:**
```
meetings/{meeting_key}/{uuid}.mp4
```

**Upload Process:**
1. Validate file (max 500MB, supported formats)
2. Create meeting record in InsForge
3. Generate signed upload URL
4. Upload to GCS
5. Confirm upload status
6. Start transcription

**Retry Logic:**
- Max 3 retries for GCS uploads
- Exponential backoff (2s, 4s, 8s)
- 5-minute timeout per upload attempt
- Automatic fallback to local storage on failure

## Transcription Pipeline

### Groq Whisper Integration

**Process:**
1. Fetch video from GCS (signed URL or direct download)
2. Send to Groq Whisper API
3. Receive transcript with timestamps
4. Store in InsForge with segments

**Timing:**
- Small files (<19MB): Single API call
- Large files (>19MB): Chunked processing (19MB chunks)
- Typical: 1-3 minutes for 30-minute meeting

**Output:**
- Full transcript text
- Language detection
- Duration in seconds
- Timestamped segments (start/end times)

## InsForge Integration

### Database Schema

**Tables:**
- `meetings`: Meeting metadata and processing status
- `media_files`: Video storage information
- `transcript_segments`: Timestamped transcript chunks
- `action_items`: Extracted action items with review status
- `audit_events`: Complete audit trail
- `team_members`: Email to GitHub handle mapping

**Data Flow:**
1. Meeting created on upload
2. Media file record created
3. Transcript segments stored after transcription
4. Action items persisted after AI extraction
5. Review status tracked per item
6. Audit events logged for all state changes

### API Endpoints

**Media Processing:**
- `POST /media/direct-upload` - Upload video directly
- `POST /media/uploads` - Prepare upload with signed URL
- `POST /media/{id}/confirm-upload` - Mark upload complete
- `POST /media/{id}/transcribe` - Start transcription

**Meeting Processing:**
- `POST /ingest` - Text transcript ingestion
- `POST /ingest/file` - File transcript ingestion
- `GET /meetings/{id}` - Get meeting details
- `POST /meetings/{id}/ask` - Q&A over transcript

**Review & Dispatch:**
- `POST /meetings/{id}/action-items/{item_id}/review` - Review action item
- `POST /meetings/{id}/dispatch` - Dispatch approved items to GitHub

**Team Management:**
- `POST /join` - Map email to GitHub handle

## LangGraph AI Workflow

### Workflow Stages

1. **Extract**: AI extracts action items, decisions, risks
2. **Resolve**: Normalize and deduplicate items
3. **Review**: Human interrupt for approval
4. **Dedup**: Remove duplicates
5. **Execute**: Dispatch to GitHub
6. **Audit**: Log all actions

### Human-in-the-Loop

**Review Process:**
1. AI extracts action items with confidence scores
2. Items persisted to InsForge with status "PENDING_REVIEW"
3. Human reviews each item (APPROVE/REJECT/EDIT)
4. Approved items marked for dispatch
5. Dispatch creates GitHub issues idempotently

## GitHub Integration

### Dispatch Process

**Prerequisites:**
- Meeting status: "AWAITING_REVIEW"
- At least one approved action item
- Valid GITHUB_TOKEN in environment

**Issue Creation:**
- One GitHub issue per approved action item
- Assignee mapped from team_members table
- Labels based on priority and classification
- Idempotent: checks for existing issues before creating

## Configuration Requirements

### Environment Variables

**Required:**
- `INSFORGE_URL` - InsForge instance URL
- `INSFORGE_API_KEY` - Server-side API key
- `GROQ_API_KEY` - Groq API key for transcription
- `GCS_MEDIA_BUCKET` - GCS bucket name
- `GCP_PROJECT_ID` - GCP project ID

**Optional:**
- `GCS_SERVICE_ACCOUNT_EMAIL` - For IAM SignBlob mode
- `GOOGLE_APPLICATION_CREDENTIALS` - SA JSON key path
- `GITHUB_TOKEN` - GitHub personal access token
- `GITHUB_REPO` - Target repository
- `MEDIA_MAX_UPLOAD_BYTES` - Max file size (default 500MB)
- `MEDIA_SIGNED_URL_TTL_MINUTES` - URL TTL (default 15)
- `DRY_RUN` - Disable actual GitHub dispatch

## Error Handling

**Fallback Mechanisms:**
- GCS upload failure → Local temp storage
- Signed URL failure → Direct GCS SDK download
- Transcription failure → Mock transcript for testing
- GitHub dispatch failure → Logged in audit events

**Error Types:**
- `MediaConfigurationError` - Missing media config
- `InsForgeConfigurationError` - Missing InsForge config
- `LookupError` - Resource not found
- `ValueError` - Invalid input
- `HTTPException` - API errors

## Performance Characteristics

**Typical Timings:**
- 10MB video: ~30 seconds total
- 50MB video: ~2 minutes total
- 100MB video: ~4 minutes total
- 500MB video: ~8-10 minutes total

**Bottlenecks:**
1. GCS upload (network dependent)
2. Groq transcription (API rate limits)
3. AI extraction (LLM response time)

**Optimizations:**
- Chunked processing for large files
- Retry logic with exponential backoff
- Parallel processing where possible
- Caching of signed URLs
