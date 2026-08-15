"""API routes — the machine interface for the agentic system.

Requirement 4: A machine can drive it. Another program can run the whole flow
end to end without a human clicking through the interface.
"""
import logging
import shutil
import os
from typing import List

from fastapi import APIRouter, HTTPException, UploadFile, File

from backend.models import (
    StartRunRequest, ReviewSubmission, RunStateResponse, CostReport, HealthResponse,
)
from backend.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# The compiled graph is injected from main.py at startup
_graph = None


def set_graph(graph):
    """Called by main.py to inject the compiled graph."""
    global _graph
    _graph = graph


def _get_graph():
    if _graph is None:
        raise HTTPException(status_code=503, detail="Agent graph not initialized")
    return _graph


# ─── Health ──────────────────────────────────────────────
@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="1.0.0", mock_llm=settings.mock_llm)


# ─── Start Run ───────────────────────────────────────────
@router.post("/run/start", response_model=RunStateResponse)
async def start_run(req: StartRunRequest):
    """Start the agent pipeline. It will pause at human_review_gate (or skip if no findings)."""
    graph = _get_graph()
    config = {"configurable": {"thread_id": req.thread_id}}

    initial_state = {
        "thread_id": req.thread_id,
        "document_paths": req.document_paths,
        "documents": [],
        "extracted_facts": [],
        "conflicts": [],
        "findings": [],
        "human_review_status": "",
        "deliverable": "",
        "current_stage": "",
        "error": "",
        "retry_count": 0,
        "injection_flags": [],
        "stage_logs": [],
        "is_incremental": False,
        "changed_sections": [],
    }

    try:
        async for _event in graph.astream(initial_state, config):
            pass  # Stream through steps until interrupted or complete

        state = await graph.aget_state(config)
        vals = state.values

        # Determine overall status
        status = "paused_for_review"
        if vals.get("human_review_status") == "no_findings":
            status = "completed"
        if vals.get("error"):
            status = "error"

        return RunStateResponse(
            thread_id=req.thread_id,
            status=status,
            current_stage=vals.get("current_stage", ""),
            findings=vals.get("findings", []),
            conflicts=vals.get("conflicts", []),
            injection_flags=vals.get("injection_flags", []),
            deliverable=vals.get("deliverable"),
            error=vals.get("error"),
        )

    except Exception as e:
        logger.error(f"start_run failed for {req.thread_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline error: {type(e).__name__}: {e}")


# ─── Get State ───────────────────────────────────────────
@router.get("/run/state/{thread_id}", response_model=RunStateResponse)
async def get_state(thread_id: str):
    """Get the current state of a run."""
    graph = _get_graph()
    config = {"configurable": {"thread_id": thread_id}}

    state = await graph.aget_state(config)
    if not state or not state.values:
        raise HTTPException(status_code=404, detail=f"Thread '{thread_id}' not found")

    vals = state.values
    status = vals.get("human_review_status", "unknown")
    if vals.get("deliverable"):
        status = "completed"
    elif vals.get("error"):
        status = "error"

    return RunStateResponse(
        thread_id=thread_id,
        status=status,
        current_stage=vals.get("current_stage", ""),
        findings=vals.get("findings", []),
        conflicts=vals.get("conflicts", []),
        injection_flags=vals.get("injection_flags", []),
        deliverable=vals.get("deliverable"),
        error=vals.get("error"),
    )


# ─── Submit Review ───────────────────────────────────────
@router.post("/run/submit_review/{thread_id}", response_model=RunStateResponse)
async def submit_review(thread_id: str, req: ReviewSubmission):
    """Submit human review decisions and resume the pipeline.

    Requirement 3: Approve or reject item by item. Rejecting one finding
    does not discard the rest.
    """
    graph = _get_graph()
    config = {"configurable": {"thread_id": thread_id}}

    # Update state with the human's decisions
    await graph.aupdate_state(
        config,
        {
            "findings": req.findings,
            "conflicts": req.conflicts if req.conflicts else [],
            "human_review_status": "completed",
        },
        as_node="human_review_gate",
    )

    # Resume the graph
    try:
        async for _event in graph.astream(None, config):
            pass

        final = await graph.aget_state(config)
        vals = final.values

        return RunStateResponse(
            thread_id=thread_id,
            status="completed",
            current_stage=vals.get("current_stage", ""),
            findings=vals.get("findings", []),
            conflicts=vals.get("conflicts", []),
            injection_flags=vals.get("injection_flags", []),
            deliverable=vals.get("deliverable"),
            error=vals.get("error"),
        )

    except Exception as e:
        logger.error(f"submit_review failed for {thread_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Resume error: {type(e).__name__}: {e}")


# ─── Cost Report (Requirement 10) ────────────────────────
@router.get("/run/cost/{thread_id}", response_model=CostReport)
async def get_cost_report(thread_id: str):
    """Report what the run spent and where time went, stage by stage."""
    graph = _get_graph()
    config = {"configurable": {"thread_id": thread_id}}

    state = await graph.aget_state(config)
    if not state or not state.values:
        raise HTTPException(status_code=404, detail=f"Thread '{thread_id}' not found")

    logs = state.values.get("stage_logs", [])
    total = sum(s.get("duration_seconds", 0) for s in logs)

    return CostReport(thread_id=thread_id, total_duration_seconds=round(total, 3), stages=logs)


# ─── Upload Documents ────────────────────────────────────
@router.post("/documents/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload documents to the watched directory for processing."""
    saved = []
    for file in files:
        dest = os.path.join(settings.watched_dir, file.filename)
        try:
            with open(dest, "wb") as f:
                content = await file.read()
                f.write(content)
            saved.append({"filename": file.filename, "size_bytes": len(content), "path": dest})
        except Exception as e:
            saved.append({"filename": file.filename, "error": str(e)})

    return {"uploaded": len(saved), "files": saved}
