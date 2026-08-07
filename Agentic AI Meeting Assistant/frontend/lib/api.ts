const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface IngestRequest {
  transcript: string;
  meeting_date: string;
  title: string;
  meeting_id?: string;
}

export interface ReviewRequest {
  reviewer_name: string;
  decision: 'APPROVED' | 'EDITED' | 'REJECTED' | 'REEXTRACTION_REQUESTED';
  note?: string;
  final_title?: string;
  priority?: 'HIGH' | 'MEDIUM' | 'LOW';
  resolved_due_date?: string;
  github_assignee_login?: string;
  final_owner_name?: string;
}

export interface AskRequest {
  question: string;
}

export interface ActionItem {
  id: string;
  title: string;
  classification: 'EXPLICIT_COMMITMENT' | 'NEEDS_CONFIRMATION' | 'DISCUSSION_ONLY';
  quote_provenance: string;
  speaker_name: string;
  confidence_score?: number;
  review_status?: 'APPROVED' | 'REJECTED' | 'PENDING';
  github_assignee_login?: string;
  suggested_github_login?: string;
  final_owner_name?: string;
  proposed_owner_name?: string;
  priority?: string;
  due_date?: string;
}

export interface MeetingData {
  meeting_id: string;
  review?: {
    payload: {
      summary?: string;
      decisions?: string[];
      open_questions?: string[];
      risks_or_blockers?: string[];
      items?: ActionItem[];
    };
  };
}

export interface DispatchResult {
  title: string;
  status: string;
  html_url?: string;
  dry_run?: boolean;
  action_item_id?: string;
  result?: {
    issue_url?: string;
    dry_run?: boolean;
  };
}

export interface AuditEvent {
  event_type: string;
  actor_type: string;
  actor_name?: string;
  created_at: string;
}

export interface MeetingDetails {
  meeting: any;
  action_items: ActionItem[];
  audit_events: AuditEvent[];
}

export async function ingestText(data: IngestRequest): Promise<MeetingData> {
  const response = await fetch(`${API_URL}/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function ingestFile(file: File): Promise<MeetingData> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await fetch(`${API_URL}/ingest/file`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function uploadMedia(file: File, onProgress?: (progress: number) => void): Promise<{ meeting_id: string; media_id: string; review: any }> {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${API_URL}/media/direct-upload`, {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'Upload failed');
  }
  
  const data = await response.json();
  
  // Return the meeting_id and review data for the UI
  return {
    meeting_id: data.meeting_id,
    media_id: data.media_id,
    review: data.review
  };
}

export async function reviewActionItem(
  meetingId: string,
  actionItemId: string,
  data: ReviewRequest
): Promise<ActionItem> {
  const response = await fetch(`${API_URL}/meetings/${meetingId}/action-items/${actionItemId}/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function dispatchMeeting(meetingId: string): Promise<DispatchResult[]> {
  const response = await fetch(`${API_URL}/meetings/${meetingId}/dispatch`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error(await response.text());
  const data = await response.json();
  return data.results || [];
}

export async function askQuestion(meetingId: string, question: string): Promise<{ answer: string }> {
  const response = await fetch(`${API_URL}/meetings/${meetingId}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function getMeetingDetails(meetingId: string): Promise<MeetingDetails> {
  const response = await fetch(`${API_URL}/meetings/${meetingId}`);
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function getHealth(): Promise<{ status: string; dry_run: boolean }> {
  const response = await fetch(`${API_URL}/health`);
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}
