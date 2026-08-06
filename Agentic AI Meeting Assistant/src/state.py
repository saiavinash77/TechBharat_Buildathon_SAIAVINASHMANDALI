from typing import List, Literal, Optional, TypedDict
from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    action_title: str = Field(description="Clear, actionable task summary")
    owner_name: str = Field(default="Unassigned", description="Person who explicitly committed, otherwise Unassigned")
    speaker_name: str = Field(default="Unknown", description="Speaker who made the statement; must be verified by a reviewer")
    classification: Literal["EXPLICIT_COMMITMENT", "NEEDS_CONFIRMATION", "DISCUSSION_ONLY"] = Field(
        default="DISCUSSION_ONLY",
        description="Strict accountability class based only on the direct statement",
    )
    owner_explicitly_accepted: bool = Field(default=False)
    extraction_reason: str = Field(default="")
    raw_due_date_mention: str = Field(default="", description="Exact date phrasing from transcript")
    resolved_due_date: Optional[str] = Field(default=None, description="YYYY-MM-DD format")
    priority: str = Field(default="MEDIUM", description="HIGH, MEDIUM, or LOW")
    confidence_score: float = Field(default=0.0, description="0.0 to 1.0")
    quote_provenance: str = Field(default="", description="Exact transcript sentence this came from")
    owner_resolution_status: Literal["RESOLVED", "UNRESOLVED", "UNASSIGNED"] = Field(
        default="UNASSIGNED",
        description="Whether owner_name mapped to team roster",
    )
    suggested_github_login: Optional[str] = Field(default=None, description="GitHub login from roster when resolved")


class MeetingRecord(BaseModel):
    executive_summary: str = Field(default="")
    decisions_made: List[str] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)
    risks_or_blockers: List[str] = Field(default_factory=list)
    action_items: List[ActionItem] = Field(default_factory=list)


class AgentState(TypedDict, total=False):
    transcript: str
    meeting_date: str
    meeting_id: Optional[str]
    audio_file_path: Optional[str]
    media_id: Optional[str]
    
    # Extraction outputs
    extracted: Optional[MeetingRecord]
    
    # Human review
    human_feedback: Optional[dict]
    approved_items: List[dict]
    rejected_items: List[dict]
    
    # Execution
    action_hashes: List[str]
    execution_results: List[dict]
    
    # Error handling
    error: Optional[str]
