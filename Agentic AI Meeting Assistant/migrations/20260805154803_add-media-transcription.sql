-- Raw media belongs in a private GCS bucket. InsForge stores only durable
-- metadata, processing state, and timestamped transcript evidence.

CREATE TABLE public.media_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES public.meetings(id) ON DELETE CASCADE,
    storage_provider TEXT NOT NULL DEFAULT 'GCS' CHECK (storage_provider = 'GCS'),
    bucket_name TEXT NOT NULL,
    object_key TEXT NOT NULL UNIQUE,
    original_filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    size_bytes BIGINT NOT NULL CHECK (size_bytes > 0 AND size_bytes <= 524288000),
    upload_status TEXT NOT NULL DEFAULT 'AWAITING_UPLOAD'
        CHECK (upload_status IN ('AWAITING_UPLOAD', 'UPLOADED', 'FAILED', 'DELETED')),
    transcription_status TEXT NOT NULL DEFAULT 'NOT_STARTED'
        CHECK (transcription_status IN ('NOT_STARTED', 'PROCESSING', 'COMPLETED', 'FAILED')),
    transcription_model TEXT,
    transcript_language TEXT,
    duration_seconds NUMERIC(12,3),
    transcription_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX media_files_meeting_id_idx ON public.media_files (meeting_id, created_at DESC);
CREATE INDEX media_files_processing_idx ON public.media_files (upload_status, transcription_status);

CREATE TABLE public.transcript_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES public.meetings(id) ON DELETE CASCADE,
    media_file_id UUID NOT NULL REFERENCES public.media_files(id) ON DELETE CASCADE,
    segment_index INTEGER NOT NULL CHECK (segment_index >= 0),
    start_seconds NUMERIC(12,3) NOT NULL CHECK (start_seconds >= 0),
    end_seconds NUMERIC(12,3) NOT NULL CHECK (end_seconds >= start_seconds),
    text TEXT NOT NULL,
    average_log_probability NUMERIC(8,5),
    no_speech_probability NUMERIC(8,5),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (media_file_id, segment_index)
);

CREATE INDEX transcript_segments_meeting_time_idx
    ON public.transcript_segments (meeting_id, start_seconds);

ALTER TABLE public.media_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transcript_segments ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.media_files FROM anon, authenticated;
REVOKE ALL ON public.transcript_segments FROM anon, authenticated;
