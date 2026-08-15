"""Agent state definition — the single source of truth for all pipeline data."""
from typing import TypedDict, List, Optional
from dataclasses import dataclass, field
import time


class Finding(TypedDict):
    """A single compliance finding."""
    id: str
    issue: str
    source: str
    source_location: str  # exact page/paragraph reference
    status: str  # "pending", "approved", "rejected"
    confidence: float  # 0.0 to 1.0


class ExtractedFact(TypedDict):
    """A fact extracted from a source document."""
    fact: str
    source: str
    source_location: str  # exact page/paragraph reference
    confidence: float


class Conflict(TypedDict):
    """When two documents disagree."""
    id: str
    description: str
    source_a: str
    source_a_location: str
    source_b: str
    source_b_location: str
    status: str  # "pending", "resolved_a", "resolved_b", "rejected"


class StageLog(TypedDict):
    """Timing and cost for a single pipeline stage."""
    stage: str
    started_at: float
    finished_at: float
    duration_seconds: float
    status: str  # "success", "failed", "skipped", "retried"
    detail: str


class AgentState(TypedDict):
    """Full pipeline state — persisted by checkpointer."""
    thread_id: str

    # Document ingestion
    document_paths: List[str]
    documents: List[dict]  # parsed doc content with metadata

    # Extraction
    extracted_facts: List[ExtractedFact]

    # Conflict detection
    conflicts: List[Conflict]

    # Rule checking
    findings: List[Finding]

    # Human review
    human_review_status: str  # "pending", "approved", "completed"

    # Deliverable
    deliverable: str

    # Pipeline control
    current_stage: str
    error: str
    retry_count: int

    # Injection defense
    injection_flags: List[dict]

    # Cost tracking
    stage_logs: List[StageLog]

    # Incremental updates
    is_incremental: bool
    changed_sections: List[str]
