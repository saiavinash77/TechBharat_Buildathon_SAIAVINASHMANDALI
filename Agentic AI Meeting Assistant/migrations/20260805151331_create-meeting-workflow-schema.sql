-- Safety-first meeting workflow. Application tables live in public; InsForge
-- managed schemas are intentionally not modified here.

CREATE TABLE public.meetings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_key TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL DEFAULT 'Untitled meeting',
    meeting_date DATE NOT NULL,
    transcript_text TEXT NOT NULL,
    transcript_hash CHAR(64) NOT NULL,
    processing_status TEXT NOT NULL DEFAULT 'RECEIVED'
        CHECK (processing_status IN ('RECEIVED', 'EXTRACTING', 'AWAITING_REVIEW', 'COMPLETED', 'FAILED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX meetings_transcript_hash_idx ON public.meetings (transcript_hash);
CREATE INDEX meetings_created_at_idx ON public.meetings (created_at DESC);

CREATE TABLE public.action_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES public.meetings(id) ON DELETE CASCADE,
    original_title TEXT NOT NULL,
    final_title TEXT NOT NULL,
    speaker_name TEXT NOT NULL,
    quote_provenance TEXT NOT NULL,
    classification TEXT NOT NULL
        CHECK (classification IN ('EXPLICIT_COMMITMENT', 'NEEDS_CONFIRMATION', 'DISCUSSION_ONLY')),
    proposed_owner_name TEXT,
    final_owner_name TEXT,
    github_assignee_login TEXT,
    owner_explicitly_accepted BOOLEAN NOT NULL DEFAULT FALSE,
    raw_due_date_mention TEXT,
    resolved_due_date DATE,
    priority TEXT NOT NULL DEFAULT 'MEDIUM'
        CHECK (priority IN ('HIGH', 'MEDIUM', 'LOW')),
    confidence_score NUMERIC(3,2) NOT NULL DEFAULT 0
        CHECK (confidence_score >= 0 AND confidence_score <= 1),
    extraction_reason TEXT NOT NULL DEFAULT '',
    original_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    review_status TEXT NOT NULL DEFAULT 'PENDING_REVIEW'
        CHECK (review_status IN ('PENDING_REVIEW', 'APPROVED', 'REJECTED', 'REEXTRACTION_REQUESTED')),
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    dispatch_status TEXT NOT NULL DEFAULT 'NOT_READY'
        CHECK (dispatch_status IN ('NOT_READY', 'NOT_ELIGIBLE', 'PENDING', 'PROCESSING', 'DISPATCHED', 'FAILED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Accountability cannot be inferred from a mention of a person's name.
    CHECK (
        classification <> 'EXPLICIT_COMMITMENT'
        OR (owner_explicitly_accepted = TRUE AND proposed_owner_name IS NOT NULL)
    ),
    CHECK (
        github_assignee_login IS NULL
        OR (classification = 'EXPLICIT_COMMITMENT' AND owner_explicitly_accepted = TRUE)
    )
);

CREATE INDEX action_items_meeting_id_idx ON public.action_items (meeting_id);
CREATE INDEX action_items_review_status_idx ON public.action_items (review_status, dispatch_status);
CREATE INDEX action_items_classification_idx ON public.action_items (classification);

CREATE TABLE public.action_item_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action_item_id UUID NOT NULL REFERENCES public.action_items(id) ON DELETE CASCADE,
    reviewer_name TEXT NOT NULL,
    decision TEXT NOT NULL
        CHECK (decision IN ('APPROVED', 'EDITED', 'REJECTED', 'REEXTRACTION_REQUESTED')),
    reviewer_note TEXT NOT NULL DEFAULT '',
    original_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    final_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX action_item_reviews_action_item_id_idx
    ON public.action_item_reviews (action_item_id, created_at DESC);

CREATE TABLE public.workflow_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL UNIQUE REFERENCES public.meetings(id) ON DELETE CASCADE,
    thread_id TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL
        CHECK (status IN ('RUNNING', 'AWAITING_REVIEW', 'COMPLETED', 'FAILED')),
    checkpoint_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.dispatch_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action_item_id UUID NOT NULL UNIQUE REFERENCES public.action_items(id) ON DELETE CASCADE,
    idempotency_key CHAR(64) NOT NULL UNIQUE,
    target TEXT NOT NULL DEFAULT 'GITHUB_ISSUES'
        CHECK (target = 'GITHUB_ISSUES'),
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'PROCESSING', 'DISPATCHED', 'FAILED')),
    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    request_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    response_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    github_issue_number INTEGER,
    github_issue_url TEXT,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX dispatch_attempts_status_idx ON public.dispatch_attempts (status, updated_at);

CREATE TABLE public.audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES public.meetings(id) ON DELETE CASCADE,
    action_item_id UUID REFERENCES public.action_items(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    actor_type TEXT NOT NULL CHECK (actor_type IN ('SYSTEM', 'REVIEWER')),
    actor_name TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX audit_events_meeting_id_idx ON public.audit_events (meeting_id, created_at DESC);
CREATE INDEX audit_events_action_item_id_idx ON public.audit_events (action_item_id, created_at DESC);

-- The buildathon MVP uses server-side FastAPI access only. Do not expose
-- meeting transcripts or review data directly through client-side PostgREST.
ALTER TABLE public.meetings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.action_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.action_item_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workflow_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dispatch_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_events ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.meetings FROM anon, authenticated;
REVOKE ALL ON public.action_items FROM anon, authenticated;
REVOKE ALL ON public.action_item_reviews FROM anon, authenticated;
REVOKE ALL ON public.workflow_runs FROM anon, authenticated;
REVOKE ALL ON public.dispatch_attempts FROM anon, authenticated;
REVOKE ALL ON public.audit_events FROM anon, authenticated;
