"""Test: Kill & Resume — Requirement 2.

"Kill the process in the middle of a run and start it again.
It continues from where it left off, and no finished work is lost."

This test runs without a live API key.
"""
import pytest
from langgraph.checkpoint.memory import MemorySaver

from backend.agent.graph import build_graph


@pytest.mark.asyncio
async def test_resume_after_interrupt():
    """Start a run, let it pause at review_gate, create a NEW graph instance,
    and verify it can resume from the checkpoint — no finished work lost."""

    # Shared checkpointer (simulates persistent storage)
    checkpointer = MemorySaver()

    # --- RUN 1: start pipeline, it should pause at human_review_gate ---
    graph_1 = build_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "resume-test-1"}}

    initial_state = {
        "thread_id": "resume-test-1",
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

    async for _ in graph_1.astream(initial_state, config):
        pass

    state_after_pause = await graph_1.aget_state(config)
    assert state_after_pause.values.get("findings"), "Should have findings before review gate"
    assert len(state_after_pause.values.get("stage_logs", [])) > 0, "Stage logs should exist"

    # --- SIMULATE CRASH: create a completely new graph instance ---
    graph_2 = build_graph(checkpointer=checkpointer)

    # Verify state survived the "crash"
    restored_state = await graph_2.aget_state(config)
    assert restored_state.values.get("findings") == state_after_pause.values.get("findings"), \
        "Findings should survive process restart"
    assert restored_state.values.get("extracted_facts"), "Extracted facts should survive"

    # --- RESUME: approve findings and continue ---
    approved_findings = [
        {**f, "status": "approved"} for f in restored_state.values.get("findings", [])
    ]
    await graph_2.aupdate_state(
        config,
        {"findings": approved_findings, "human_review_status": "completed"},
        as_node="human_review_gate",
    )

    async for _ in graph_2.astream(None, config):
        pass

    final_state = await graph_2.aget_state(config)
    assert final_state.values.get("deliverable"), "Should have deliverable after resume"
    assert "Compliance" in final_state.values["deliverable"], "Deliverable should be a compliance report"
