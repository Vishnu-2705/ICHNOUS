"""Unit tests for Graph Builder module."""

import sys
from pathlib import Path
import networkx as nx

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fixtures import get_all_fixtures
from graph.builder import (
    build_graph,
    edge_lookup,
    get_graph_statistics,
    get_num_edges,
    get_num_nodes,
    node_lookup,
)
from models.trace import NodeType, Trace, TraceNode


def test_build_graph_basic():
    node1 = TraceNode(
        id="n1",
        type=NodeType.PLAN,
        timestamp="2026-07-30T00:00:00Z",
        content="Plan execution",
        metadata={"step": 1},
        reads_from=[],
    )
    node2 = TraceNode(
        id="n2",
        type=NodeType.TOOL_CALL,
        timestamp="2026-07-30T00:00:01Z",
        content="Call tool",
        metadata={"step": 2, "tool": "search"},
        reads_from=["n1"],
    )

    trace = Trace(
        id="t1",
        name="Basic Trace",
        description="Simple 2 node trace",
        nodes=[node1, node2],
    )

    g = build_graph(trace)

    # Output verification
    assert isinstance(g, nx.DiGraph)
    assert get_num_nodes(g) == 2
    assert get_num_edges(g) == 1

    # Node lookup & metadata verification
    n1_data = node_lookup(g, "n1")
    assert n1_data is not None
    assert n1_data["type"] == "plan"
    assert n1_data["metadata"] == {"step": 1}

    n2_data = node_lookup(g, "n2")
    assert n2_data is not None
    assert n2_data["type"] == "tool_call"
    assert n2_data["metadata"]["tool"] == "search"

    # Edge lookup verification (n1 -> n2)
    assert edge_lookup(g, "n1", "n2") is not None
    assert edge_lookup(g, "n2", "n1") is None

    # Graph statistics
    stats = get_graph_statistics(g)
    assert stats["num_nodes"] == 2
    assert stats["num_edges"] == 1
    assert stats["is_dag"] is True


def test_build_graph_with_fixtures():
    fixtures = get_all_fixtures()

    for name, trace in fixtures.items():
        g = build_graph(trace)

        assert isinstance(g, nx.DiGraph)
        assert get_num_nodes(g) == len(trace.nodes)
        assert get_num_nodes(g) > 0

        # Verify all nodes exist in graph with metadata
        for node in trace.nodes:
            n_data = node_lookup(g, node.id)
            assert n_data is not None
            assert n_data["id"] == node.id
            assert n_data["content"] == node.content
            assert n_data["timestamp"] == node.timestamp

            # Verify edges for reads_from
            for upstream_id in node.reads_from:
                assert edge_lookup(g, upstream_id, node.id) is not None

        stats = get_graph_statistics(g)
        assert stats["num_nodes"] == len(trace.nodes)
        assert stats["num_edges"] >= 0

    print("All Graph Builder unit tests passed successfully!")


if __name__ == "__main__":
    test_build_graph_basic()
    test_build_graph_with_fixtures()
