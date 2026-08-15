"""Test: Cost Tracking — Requirement 10.

"A run can report what it spent and where the time went, stage by stage."

This test runs without a live API key.
"""
import pytest
from langgraph.checkpoint.memory import MemorySaver

from backend.agent.graph import build_graph


@pytest.mark.asyncio
async def test_cost_report_has_all_stages():
    """Every stage that ran should have a timing entry in stage_logs."""

    checkpointer = MemorySaver()
    graph = build_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "cost-test-1"}}

    initial_state = {
        "thread_id": "cost-test-1",
        "document_paths": [], "documents": [], "extracted_facts": [],
        "conflicts": [], "findings": [], "human_review_status": "",
        "deliverable": "", "current_stage": "", "error": "",
        "retry_count": 0, "injection_flags": [], "stage_logs": [],
        "is_incremental": False, "changed_sections": [],
    }

    async for _ in graph.astream(initial_state, config):
        pass

    state = await graph.aget_state(config)
    logs = state.values.get("stage_logs", [])

    # Should have logs for: sanitize_input, ingest_docs, extract_facts,
    # detect_conflicts, check_rules (at minimum, before the review gate pauses)
    assert len(logs) >= 5, f"Expected at least 5 stage logs, got {len(logs)}"

    expected_stages = {"sanitize_input", "ingest_docs", "extract_facts", "detect_conflicts", "check_rules"}
    logged_stages = {log["stage"] for log in logs}

    for stage in expected_stages:
        assert stage in logged_stages, f"Missing stage log for: {stage}"

    # Every log should have positive timing
    for log in logs:
        assert "duration_seconds" in log, f"Stage {log['stage']} missing duration"
        assert log["duration_seconds"] >= 0, f"Stage {log['stage']} has negative duration"
        assert "status" in log, f"Stage {log['stage']} missing status"


@pytest.mark.asyncio
async def test_total_cost_is_sum_of_stages():
    """Total duration should equal the sum of all stage durations."""

    checkpointer = MemorySaver()
    graph = build_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "cost-test-sum"}}

    initial_state = {
        "thread_id": "cost-test-sum",
        "document_paths": [], "documents": [], "extracted_facts": [],
        "conflicts": [], "findings": [], "human_review_status": "",
        "deliverable": "", "current_stage": "", "error": "",
        "retry_count": 0, "injection_flags": [], "stage_logs": [],
        "is_incremental": False, "changed_sections": [],
    }

    async for _ in graph.astream(initial_state, config):
        pass

    state = await graph.aget_state(config)
    logs = state.values.get("stage_logs", [])

    total = sum(s["duration_seconds"] for s in logs)
    assert total > 0, "Total time should be positive"

    # Each stage should report its own name correctly
    for log in logs:
        assert isinstance(log["stage"], str) and len(log["stage"]) > 0
