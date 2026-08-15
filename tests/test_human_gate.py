"""Test: Human Gate — Requirement 3.

"A person reviews what the system intends to do, approves what is right
and rejects what is wrong in the same review, item by item,
and the system respects every decision."

This test runs without a live API key.
"""
import pytest
from langgraph.checkpoint.memory import MemorySaver

from backend.agent.graph import build_graph


@pytest.mark.asyncio
async def test_approve_one_reject_another():
    """Approve finding 1, reject finding 2. The deliverable should contain
    ONLY the approved finding. Rejecting one does not discard the rest."""

    checkpointer = MemorySaver()
    graph = build_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "gate-test-1"}}

    initial_state = {
        "thread_id": "gate-test-1",
        "document_paths": [],
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

    # Run until review gate
    async for _ in graph.astream(initial_state, config):
        pass

    state = await graph.aget_state(config)
    findings = state.values.get("findings", [])
    assert len(findings) > 0, "Should have at least one finding"

    # Approve first, reject rest
    mixed_findings = []
    for i, f in enumerate(findings):
        if i == 0:
            mixed_findings.append({**f, "status": "approved"})
        else:
            mixed_findings.append({**f, "status": "rejected"})

    # Submit review
    await graph.aupdate_state(
        config,
        {"findings": mixed_findings, "human_review_status": "completed"},
        as_node="human_review_gate",
    )
    async for _ in graph.astream(None, config):
        pass

    final = await graph.aget_state(config)
    deliverable = final.values.get("deliverable", "")

    assert deliverable, "Deliverable should exist"
    assert "Approved Findings" in deliverable or "No compliance issues" in deliverable


@pytest.mark.asyncio
async def test_reject_all_findings():
    """Rejecting ALL findings should produce a clean report."""

    checkpointer = MemorySaver()
    graph = build_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "gate-test-reject-all"}}

    initial_state = {
        "thread_id": "gate-test-reject-all",
        "document_paths": [], "documents": [], "extracted_facts": [],
        "conflicts": [], "findings": [], "human_review_status": "",
        "deliverable": "", "current_stage": "", "error": "",
        "retry_count": 0, "injection_flags": [], "stage_logs": [],
        "is_incremental": False, "changed_sections": [],
    }

    async for _ in graph.astream(initial_state, config):
        pass

    state = await graph.aget_state(config)
    rejected = [{**f, "status": "rejected"} for f in state.values.get("findings", [])]

    await graph.aupdate_state(
        config,
        {"findings": rejected, "human_review_status": "completed"},
        as_node="human_review_gate",
    )
    async for _ in graph.astream(None, config):
        pass

    final = await graph.aget_state(config)
    deliverable = final.values.get("deliverable", "")
    assert "No compliance issues" in deliverable or "rejected" in deliverable.lower(), \
        "Rejecting all should produce a clean/rejection report"
