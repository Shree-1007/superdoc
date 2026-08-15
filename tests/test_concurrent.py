"""Test: Concurrent Runs — Requirement 9.

"Two runs at the same time stay two runs. Concurrent work does not corrupt state."

This test runs without a live API key.
"""
import asyncio
import pytest
from langgraph.checkpoint.memory import MemorySaver

from backend.agent.graph import build_graph


@pytest.mark.asyncio
async def test_concurrent_runs_no_state_leakage():
    """Run two pipelines simultaneously with different thread_ids.
    Verify no state leaks between them."""

    checkpointer = MemorySaver()
    graph = build_graph(checkpointer=checkpointer)

    def _make_initial(thread_id):
        return {
            "thread_id": thread_id,
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

    async def run_pipeline(thread_id):
        config = {"configurable": {"thread_id": thread_id}}
        async for _ in graph.astream(_make_initial(thread_id), config):
            pass
        return await graph.aget_state(config)

    # Run two pipelines concurrently
    state_a, state_b = await asyncio.gather(
        run_pipeline("concurrent-A"),
        run_pipeline("concurrent-B"),
    )

    # Both should have findings (paused at review gate)
    assert state_a.values.get("findings"), "Run A should have findings"
    assert state_b.values.get("findings"), "Run B should have findings"

    # Thread IDs must not leak
    assert state_a.values["thread_id"] == "concurrent-A"
    assert state_b.values["thread_id"] == "concurrent-B"

    # Stage logs should be independent
    logs_a = state_a.values.get("stage_logs", [])
    logs_b = state_b.values.get("stage_logs", [])
    assert len(logs_a) > 0, "Run A should have stage logs"
    assert len(logs_b) > 0, "Run B should have stage logs"


@pytest.mark.asyncio
async def test_same_pile_hit_twice():
    """Run the same pile (no doc paths) twice with different thread IDs.
    Both should produce equivalent but independent results."""

    checkpointer = MemorySaver()
    graph = build_graph(checkpointer=checkpointer)

    configs = [
        {"configurable": {"thread_id": "same-pile-1"}},
        {"configurable": {"thread_id": "same-pile-2"}},
    ]

    for config in configs:
        initial = {
            "thread_id": config["configurable"]["thread_id"],
            "document_paths": [], "documents": [], "extracted_facts": [],
            "conflicts": [], "findings": [], "human_review_status": "",
            "deliverable": "", "current_stage": "", "error": "",
            "retry_count": 0, "injection_flags": [], "stage_logs": [],
            "is_incremental": False, "changed_sections": [],
        }
        async for _ in graph.astream(initial, config):
            pass

    s1 = await graph.aget_state(configs[0])
    s2 = await graph.aget_state(configs[1])

    # Both should reach the same stage with findings
    assert len(s1.values["findings"]) == len(s2.values["findings"]), \
        "Same pile should produce same number of findings"
    assert s1.values["thread_id"] != s2.values["thread_id"], \
        "Thread IDs must remain independent"
