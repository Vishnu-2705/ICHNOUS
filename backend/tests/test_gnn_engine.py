"""Unit tests for GNN Regression Intelligence Engine."""

import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fixtures import get_retrieval_failure_trace
from graph.builder import build_graph
from regression.intelligence import run_gnn_regression_intelligence


def test_gnn_regression_intelligence_pipeline():
    trace = get_retrieval_failure_trace()
    g = build_graph(trace)

    gnn_out = run_gnn_regression_intelligence(trace, g)

    assert gnn_out.trace_id == "trace_retrieval"
    assert gnn_out.engine_version == "v2.4-HeteroGraphTransformer"
    assert 0.0 <= gnn_out.regression_probability <= 1.0
    assert 0.0 <= gnn_out.failure_probability <= 1.0
    assert gnn_out.failure_category in ("Retrieval", "Tool", "Coordination", "Reasoning", "Unknown")
    assert len(gnn_out.vulnerable_nodes) > 0
    assert len(gnn_out.explanation_subgraph_nodes) > 0
    assert gnn_out.predicted_root_cause_node_id in g.nodes


if __name__ == "__main__":
    test_gnn_regression_intelligence_pipeline()
    print("GNN Regression Intelligence Engine unit tests passed successfully!")
