"""Unit tests for Anomaly Detection module."""

import sys
from pathlib import Path
import networkx as nx

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fixtures import (
    get_coordination_failure_trace,
    get_retrieval_failure_trace,
    get_tool_failure_trace,
)
from graph.analyzer import detect_anomalies
from graph.builder import build_graph
from models.trace import AnomalyFlag, NodeType, Trace, TraceNode


def test_detect_anomalies_synthetic():
    # Construct a synthetic graph with nodes testing all 6 anomaly categories
    nodes = [
        # Normal node
        TraceNode(
            id="n_normal",
            type=NodeType.PLAN,
            timestamp="2026-07-30T14:00:00Z",
            content="Normal plan",
            metadata={"latency_ms": 100},
        ),
        # 1. High latency node (> 5000ms)
        TraceNode(
            id="n_latency",
            type=NodeType.REASONING,
            timestamp="2026-07-30T14:00:01Z",
            content="Slow reasoning",
            metadata={"latency_ms": 6500},
            reads_from=["n_normal"],
        ),
        # 2. Tool error node
        TraceNode(
            id="n_error",
            type=NodeType.TOOL_CALL,
            timestamp="2026-07-30T14:00:02Z",
            content="Failed tool call",
            metadata={"error": "rate_limit_exceeded"},
            reads_from=["n_normal"],
        ),
        # 3. Low retrieval relevance node (< 0.6)
        TraceNode(
            id="n_relevance",
            type=NodeType.TOOL_CALL,
            timestamp="2026-07-30T14:00:03Z",
            content="Low quality search",
            metadata={"relevance_score": 0.35},
            reads_from=["n_normal"],
        ),
        # 4. Timeout node
        TraceNode(
            id="n_timeout",
            type=NodeType.DECISION,
            timestamp="2026-07-30T14:00:04Z",
            content="Timed out decision",
            metadata={"error": "execution_timeout"},
            reads_from=["n_normal"],
        ),
        # 5. Large response node
        TraceNode(
            id="n_large_response",
            type=NodeType.OBSERVATION,
            timestamp="2026-07-30T14:00:05Z",
            content="Large output",
            metadata={"response_truncated": True, "response_completeness": 0.40},
            reads_from=["n_normal"],
        ),
        # 6. Cycle nodes (n_cycle1 -> n_cycle2 -> n_cycle1)
        TraceNode(
            id="n_cycle1",
            type=NodeType.DELEGATION,
            timestamp="2026-07-30T14:00:06Z",
            content="Delegation A",
            reads_from=["n_cycle2"],
        ),
        TraceNode(
            id="n_cycle2",
            type=NodeType.DELEGATION,
            timestamp="2026-07-30T14:00:07Z",
            content="Delegation B",
            reads_from=["n_cycle1"],
        ),
    ]

    trace = Trace(
        id="trace_synthetic",
        name="Synthetic Anomaly Test Trace",
        description="Trace with known anomalies",
        nodes=nodes,
    )

    g = build_graph(trace)
    anomalies = detect_anomalies(g)

    assert isinstance(anomalies, list)
    assert len(anomalies) > 0
    assert all(isinstance(a, AnomalyFlag) for a in anomalies)

    detected_types = {a.anomaly_type for a in anomalies}
    expected_types = {
        "high_latency",
        "tool_error",
        "low_relevance",
        "timeout",
        "large_response",
        "cycle",
    }

    # Verify all 6 anomaly categories were detected
    for exp in expected_types:
        assert exp in detected_types, f"Expected anomaly type '{exp}' was not detected in synthetic trace!"

    print("Synthetic trace anomaly detection test passed successfully!")


def test_detect_anomalies_fixtures():
    # 1. Test Retrieval Failure Fixture
    g_retrieval = build_graph(get_retrieval_failure_trace())
    anomalies_retrieval = detect_anomalies(g_retrieval)
    types_retrieval = {a.anomaly_type for a in anomalies_retrieval}
    assert "low_relevance" in types_retrieval

    # 2. Test Tool Failure Fixture
    g_tool = build_graph(get_tool_failure_trace())
    anomalies_tool = detect_anomalies(g_tool)
    types_tool = {a.anomaly_type for a in anomalies_tool}
    assert "high_latency" in types_tool or "large_response" in types_tool or "tool_error" in types_tool

    # 3. Test Coordination Failure Fixture
    g_coord = build_graph(get_coordination_failure_trace())
    anomalies_coord = detect_anomalies(g_coord)
    types_coord = {a.anomaly_type for a in anomalies_coord}
    assert "cycle" in types_coord or "timeout" in types_coord

    print("Fixture trace anomaly detection test passed successfully!")


if __name__ == "__main__":
    test_detect_anomalies_synthetic()
    test_detect_anomalies_fixtures()
