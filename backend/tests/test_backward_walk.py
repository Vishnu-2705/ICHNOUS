"""Unit tests for Backward Causal Walk algorithm."""

import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fixtures import (
    get_coordination_failure_trace,
    get_retrieval_failure_trace,
    get_tool_failure_trace,
)
from graph.analyzer import backward_walk, compute_divergence
from graph.builder import build_graph
from models.trace import NodeType, RootCauseCandidate, Trace, TraceNode


def test_earliest_divergence_selection():
    """
    Test that backward walk selects the EARLIEST upstream divergence node,
    NOT the node closest to failure.
    """
    nodes = [
        # Node 0: Plan
        TraceNode(id="n0", type=NodeType.PLAN, timestamp="2026-07-30T14:00:00Z", content="Plan"),
        # Node 1: Earliest root cause (low relevance retrieval = 0.35)
        TraceNode(
            id="n1",
            type=NodeType.TOOL_CALL,
            timestamp="2026-07-30T14:00:01Z",
            content="Search tool",
            metadata={"relevance_score": 0.35},
            reads_from=["n0"],
        ),
        # Node 2: Downstream reasoning (reads bad retrieval)
        TraceNode(
            id="n2",
            type=NodeType.REASONING,
            timestamp="2026-07-30T14:00:02Z",
            content="Reasoning over bad retrieval",
            reads_from=["n1"],
        ),
        # Node 3: Downstream tool call
        TraceNode(
            id="n3",
            type=NodeType.TOOL_CALL,
            timestamp="2026-07-30T14:00:03Z",
            content="Lookup order",
            metadata={"relevance_score": 0.95},
            reads_from=["n2"],
        ),
        # Node 4: Downstream reasoning
        TraceNode(
            id="n4",
            type=NodeType.REASONING,
            timestamp="2026-07-30T14:00:04Z",
            content="Reasoning over order data",
            reads_from=["n3"],
        ),
        # Node 5: Final Answer (Failure point)
        TraceNode(
            id="n5",
            type=NodeType.FINAL_ANSWER,
            timestamp="2026-07-30T14:00:05Z",
            content="Incorrect final answer",
            reads_from=["n4"],
        ),
    ]

    trace = Trace(id="t_causal", name="Causal Chain Trace", description="Test trace", nodes=nodes)
    g = build_graph(trace)

    result = backward_walk(g)

    assert isinstance(result, RootCauseCandidate)
    # Crucial assertion: Must pick 'n1' (earliest divergence at pos 1), NOT 'n4' or 'n3'
    assert result.node_id == "n1"
    assert result.divergence_score >= 0.4
    assert result.evidence_node_ids == ["n1", "n2", "n3", "n4", "n5"]


def test_schema_mismatch_and_divergence_signals():
    nodes = [
        TraceNode(id="s0", type=NodeType.PLAN, timestamp="2026-07-30T14:00:00Z", content="Plan"),
        TraceNode(
            id="s1",
            type=NodeType.TOOL_CALL,
            timestamp="2026-07-30T14:00:01Z",
            content="Call API",
            metadata={"schema_mismatch": True, "error": "Invalid schema format"},
            reads_from=["s0"],
        ),
        TraceNode(id="s2", type=NodeType.FINAL_ANSWER, timestamp="2026-07-30T14:00:02Z", content="Done", reads_from=["s1"]),
    ]
    trace = Trace(id="t_schema", name="Schema Trace", description="Schema test", nodes=nodes)
    g = build_graph(trace)

    assert compute_divergence(g, "s1") >= 0.5
    result = backward_walk(g)
    assert result.node_id == "s1"


def test_backward_walk_fixtures():
    # 1. Retrieval Failure Fixture: Expected Root Cause = node_2 (stale retrieval)
    g_retrieval = build_graph(get_retrieval_failure_trace())
    rc_retrieval = backward_walk(g_retrieval)
    assert rc_retrieval.node_id == "node_2"

    # 2. Tool Failure Fixture: Expected Root Cause = node_5 (truncated tool output)
    g_tool = build_graph(get_tool_failure_trace())
    rc_tool = backward_walk(g_tool)
    assert rc_tool.node_id == "node_5"

    # 3. Coordination Failure Fixture: Root Cause identified in cycle
    g_coord = build_graph(get_coordination_failure_trace())
    rc_coord = backward_walk(g_coord)
    assert rc_coord.node_id in {"node_3", "node_5", "node_6", "node_8", "node_11"}

    print("All Backward Causal Walk unit tests passed successfully!")


if __name__ == "__main__":
    test_earliest_divergence_selection()
    test_schema_mismatch_and_divergence_signals()
    test_backward_walk_fixtures()
