# 🎙️ End-to-End Visual Chat Workflow

This document illustrates the complete end-to-end user journey, data processing pipeline, and safety-first human-in-the-loop review state machine in the **Agentic AI Meeting Assistant**.

---

## 🎨 Visual Workflow Diagram (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 User / Human Reviewer
    participant UI as 💬 Chainlit UI (app.py)
    participant API as ⚡ FastAPI Backend (main.py)
    participant GCS as ☁️ GCP Storage (GCS Bucket)
    participant Groq as 🧠 Groq AI (Whisper + LLaMA 3.3)
    participant Graph as 🔄 LangGraph Agent Workflow
    participant DB as 🐘 InsForge PostgreSQL DB
    participant GH as 🐙 GitHub API (Execution Engine)

    %% 1. Ingestion Phase
    rect rgb(240, 248, 255)
    note right of User: 1. INGESTION PHASE
    alt Option A: Audio/Video File Upload
        User->>UI: Attach / Drag & Drop Media (.mp4, .mp3, .wav)
        UI->>GCS: Direct Stream / Signed Upload to Private Bucket
        GCS-->>UI: Upload Confirmed
        UI->>Groq: Stream Audio to Whisper-Large-v3-Turbo
        Groq-->>UI: Return Transcript + Timestamp Evidence Segments
    else Option B: Raw Text Transcript
        User->>UI: Paste Text Transcript (>50 chars)
    end
    end

    %% 2. Agentic Extraction Phase
    rect rgb(245, 245, 245)
    note right of User: 2. AGENTIC EXTRACTION PHASE
    UI->>Graph: Invoke State Machine (transcript, meeting_id)
    Graph->>Groq: LLaMA-3.3-70B: Extract Summary & Action Candidates
    Groq-->>Graph: Structured Action Items + Timestamp Evidence
    Graph->>Graph: Classify Items (Commitment / Needs Review / Discussion Only)
    Graph->>DB: Persist Meeting, Segments & Action Candidates
    Graph->>Graph: 🛑 Native Review Interrupt (interrupt())
    Graph-->>UI: Pause Workflow & Render Candidate Review Cards
    end

    %% 3. Human-in-the-Loop Review Phase
    rect rgb(255, 250, 240)
    note right of User: 3. HUMAN-IN-THE-LOOP REVIEW PHASE
    User->>UI: Review Cards (Approve / Edit / Reject)
    alt Optional: Ask Meeting Questions
        User->>UI: "What did Avinash promise by Friday?"
        UI->>Groq: Answer from transcript context with exact quote
        Groq-->>UI: Return Evidence-Backed Answer
    end
    User->>UI: Click "✅ Approve Eligible Items"
    end

    %% 4. Execution & Audit Phase
    rect rgb(240, 255, 240)
    note right of User: 4. SAFE EXECUTION & AUDIT PHASE
    UI->>Graph: Resume Command(resume={"decision": "approve"})
    Graph->>DB: Check SHA-256 Hash Deduplication (dispatch_attempts)
    alt Approved & Not Duplicate
        Graph->>GH: Create GitHub Issue (Assigned if explicit, unassigned if needs-confirmation)
        GH-->>Graph: Issue # Created / Dry-Run Result
        Graph->>DB: Record Audit Log (audit_events)
    else Blocked (Discussion Only or Duplicate)
        Graph->>Graph: Block Side Effects (0 side effects)
    end
    Graph-->>UI: Render Execution Results Cards (Issue # & Links)
    end
```

---

## 🏛️ System Component Breakdown

| Layer | Component | Function & Responsibility |
|---|---|---|
| **User Interface** | [app.py](file:///c:/Users/sai%20avinash/OneDrive/Desktop/TechBharat/Agentic%20AI%20Meeting%20Assistant/app.py) | Conversational Chainlit Chat UI, file drag & drop, interactive review cards, evidence Q&A. |
| **Backend REST API** | [main.py](file:///c:/Users/sai%20avinash/OneDrive/Desktop/TechBharat/Agentic%20AI%20Meeting%20Assistant/main.py) | FastAPI service exposing `/media/uploads`, `/transcribe`, `/review`, `/dispatch`, `/health`. |
| **Object Storage** | [src/media.py](file:///c:/Users/sai%20avinash/OneDrive/Desktop/TechBharat/Agentic%20AI%20Meeting%20Assistant/src/media.py) | Private GCP Cloud Storage bucket (`agentic-ai-meeting-assistant-media-634824910481`) with IAM SignBlob. |
| **Speech-to-Text** | Groq Whisper | Converts raw audio/video into timestamped transcript segments in ~2 seconds. |
| **LLM Agent** | Groq LLaMA 3.3 70B | Structured candidate extraction, evidence mapping, and evidence-backed meeting Q&A. |
| **State Machine** | [src/graph.py](file:///c:/Users/sai%20avinash/OneDrive/Desktop/TechBharat/Agentic%20AI%20Meeting%20Assistant/src/graph.py) | LangGraph durable workflow with native `interrupt()` human review gate. |
| **Database** | [src/insforge_client.py](file:///c:/Users/sai%20avinash/OneDrive/Desktop/TechBharat/Agentic%20AI%20Meeting%20Assistant/src/insforge_client.py) | InsForge PostgreSQL storing meetings, segments, action items, dedup hashes, and audit logs. |
| **Safety Dispatcher** | [src/execution.py](file:///c:/Users/sai%20avinash/OneDrive/Desktop/TechBharat/Agentic%20AI%20Meeting%20Assistant/src/execution.py) | Ensures only reviewer-approved items trigger GitHub Issue creation; supports `DRY_RUN` safety mode. |

---

## 🛡️ Accountability Tri-Classification Rules

```text
               ┌──────────────────────────────────────────┐
               │    AI Extracted Candidate Action Item    │
               └────────────────────┬─────────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           ▼                        ▼                        ▼
┌────────────────────┐    ┌────────────────────┐    ┌────────────────────┐
│EXPLICIT_COMMITMENT │    │ NEEDS_CONFIRMATION │    │  DISCUSSION_ONLY   │
│ Speaker accepted   │    │ Unclear request    │    │ Idea/Question      │
└──────────┬─────────┘    └──────────┬─────────┘    └──────────┬─────────┘
           │                         │                         │
           ▼                         ▼                         ▼
   Human Review Gate         Human Review Gate         🚫 STAGE BLOCKED
   Approve & Assign         Approve Unassigned          No GitHub Issue
```
