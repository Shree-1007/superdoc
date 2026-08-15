"""LangGraph workflow construction with conditional edges and checkpointing."""
import logging
import sqlite3
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from backend.config import settings

from backend.agent.state import AgentState
from backend.agent.nodes import (
    sanitize_input,
    ingest_docs,
    extract_facts,
    detect_conflicts,
    check_rules,
    human_review_gate,
    generate_deliverable,
    route_after_check,
    route_after_sanitize,
)

logger = logging.getLogger(__name__)


def build_graph(checkpointer=None):
    """Build and compile the agent graph.
    
    Architecture:
        sanitize_input → ingest_docs → extract_facts → detect_conflicts →
        check_rules → [branch: retry | skip | human_review_gate] →
        generate_deliverable → END
    
    Branching (Requirement 1):
        - After check_rules: retry on failure (up to 3x), skip review if no findings,
          or escalate to human review
        - After sanitize_input: always continues (injections are flagged, not blocked)
    
    Interruption (Requirement 3):
        - interrupt_before=["human_review_gate"] pauses for human review
    """
    workflow = StateGraph(AgentState)

    # Register all nodes
    workflow.add_node("sanitize_input", sanitize_input)
    workflow.add_node("ingest_docs", ingest_docs)
    workflow.add_node("extract_facts", extract_facts)
    workflow.add_node("detect_conflicts", detect_conflicts)
    workflow.add_node("check_rules", check_rules)
    workflow.add_node("human_review_gate", human_review_gate)
    workflow.add_node("generate_deliverable", generate_deliverable)

    # Entry point
    workflow.set_entry_point("sanitize_input")

    # Linear edges
    workflow.add_conditional_edges("sanitize_input", route_after_sanitize, {
        "ingest_docs": "ingest_docs",
    })
    workflow.add_edge("ingest_docs", "extract_facts")
    workflow.add_edge("extract_facts", "detect_conflicts")
    workflow.add_edge("detect_conflicts", "check_rules")

    # Branching edge after check_rules (Requirement 1)
    workflow.add_conditional_edges("check_rules", route_after_check, {
        "check_rules": "check_rules",           # retry
        "human_review_gate": "human_review_gate",  # normal flow / escalate
        "generate_deliverable": "generate_deliverable",  # skip review (no findings)
    })

    # After human review → generate deliverable
    workflow.add_edge("human_review_gate", "generate_deliverable")

    # End
    workflow.add_edge("generate_deliverable", END)

    # Compile with checkpointer
    if checkpointer is None:
        conn = sqlite3.connect(settings.checkpoint_db, check_same_thread=False)
        SqliteSaver.setup(conn)
        checkpointer = SqliteSaver(conn)

    compiled = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_review_gate"],
    )

    logger.info("Agent graph compiled successfully")
    return compiled
