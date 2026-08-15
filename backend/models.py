"""Pydantic models for API request/response schemas."""
from typing import List, Optional
from pydantic import BaseModel


class StartRunRequest(BaseModel):
    thread_id: str
    document_paths: List[str] = []


class ReviewSubmission(BaseModel):
    findings: List[dict]
    conflicts: List[dict] = []


class RunStateResponse(BaseModel):
    thread_id: str
    status: str
    current_stage: Optional[str] = None
    findings: List[dict] = []
    conflicts: List[dict] = []
    injection_flags: List[dict] = []
    deliverable: Optional[str] = None
    error: Optional[str] = None


class CostReport(BaseModel):
    thread_id: str
    total_duration_seconds: float
    stages: List[dict]


class HealthResponse(BaseModel):
    status: str
    version: str
    mock_llm: bool
