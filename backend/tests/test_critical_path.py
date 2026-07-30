"""Unit tests for Critical Path Extraction module."""

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
from graph.analyzer import extract_critical_path, find_failure_node
from graph.builder import build_graph
from models.trace import NodeType, Trace, TraceNode


def test_critical_path_final_answer():
    nodes = [
        TraceNode(id="node_start", type=NodeType.PLAN, timestamp="2026-07-30T14:00:00Z", content="Plan"),
        TraceNode(id="node_step1", type=NodeType.TOOL_CALL, timestamp="2026-07-30T14:00:01Z", content="Tool", reads_from=["node_start"]),
        TraceNode(id="node_step2", type=NodeType.REASONING, timestamp="2026-07-30T14:00:02Z", content="Reasoning", reads_from=["node_step1"]),
        TraceNode(id="node_end", type=NodeType.FINAL_ANSWER, timestamp="2026-07-30T14:00:03Z", content="Final Answer", reads_from=["node_step2"]),
    ]
    trace = Trace(id="t_final", name="Final Answer Trace", description="Linear trace", nodes=nodes)
    g = build_graph(trace)

    failure_id = find_failure_node(g)
    assert failure_id == "node_end"

    path = extract_critical_path(g)
    assert path == ["node_start", "node_step1", "node_step2", "node_end"]


def test_critical_path_timeout():
    nodes = [
        TraceNode(id="n0", type=NodeType.PLAN, timestamp="2026-07-30T14:00:00Z", content="Start"),
        TraceNode(id="n1", type=NodeType.DELEGATION, timestamp="2026-07-30T14:00:01Z", content="Delegation", reads_from=["n0"]),
        TraceNode(id="n_timeout", type=NodeType.DECISION, timestamp="2026-07-30T14:00:02Z", content="Timeout", metadata={"error": "execution_timeout"}, reads_from=["n1"]),
    ]
    trace = Trace(id="t_timeout", name="Timeout Trace", description="Timeout trace", nodes=nodes)
    g = build_graph(trace)

    failure_id = find_failure_node(g)
    assert failure_id == "n_timeout"

    path = extract_critical_path(g)
    assert path == ["n0", "n1", "n_timeout"]


def test_critical_path_cycles_safety():
    # Build graph with explicit cycles: n0 -> n1 -> n2 -> n1, n2 -> n_timeout
    g = nx.DiGraph()
    g.add_node("n0", type="plan", metadata={})
    g.add_node("n1", type="delegation", metadata={})
    g.add_node("n2", type="observation", metadata={})
    g.add_node("n_timeout", type="decision", metadata={"error": "execution_timeout"})

    g.add_edge("n0", "n1")
    g.add_edge("n1", "n2")
    g.add_edge("n2", "n1")  # Cycle n1 <-> n2
    g.add_edge("n2", "n_timeout")

    assert nx.is_directed_acyclic_graph(g) is False

    failure_id = find_failure_node(g)
    assert failure_id == "n_timeout"

    # Must complete safely without infinite loops
    path = extract_critical_path(g)
    assert isinstance(path, list)
    assert path[0] == "n0"
    assert path[-1] == "n_timeout"


def test_critical_path_fixtures():
    # 1. Retrieval trace
    g_retrieval = build_graph(get_retrieval_failure_trace())
    path_retrieval = extract_critical_path(g_retrieval)
    assert len(path_retrieval) > 0
    assert path_retrieval[-1] == "node_9"  # Final answer node in retrieval fixture

    # 2. Tool trace
    g_tool = build_graph(get_tool_failure_trace())
    path_tool = extract_critical_path(g_tool)
    assert len(path_tool) > 0
    assert path_tool[-1] == "node_12"  # Final answer node in tool fixture

    # 3. Coordination trace (Timeout / Cycle)
    g_coord = build_graph(get_coordination_failure_trace())
    path_coord = extract_critical_path(g_coord)
    assert len(path_coord) > 0
    assert path_coord[-1] == "node_12"  # Timeout node in coordination fixture

    print("All Critical Path unit tests passed successfully!")


if __name__ == "__main__":
    test_critical_path_final_answer()
    test_critical_path_timeout()
    test_critical_path_cycles_safety()
    test_critical_path_fixtures()
