"""
Unit tests for Neo4j Property Graph Adapter.
"""

import sys
from pathlib import Path
import pytest
import networkx as nx

# Ensure sys.path includes backend and project root
backend_dir = Path(__file__).resolve().parent.parent
project_dir = backend_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

from agent365.adapters.neo4j import Neo4jAdapter


class TestNeo4jAdapter:
    def test_sync_graph_mock_mode(self):
        adapter = Neo4jAdapter(uri="bolt://localhost:7687")

        g = nx.DiGraph()
        g.add_node("n1", type="plan", content="plan query")
        g.add_node("n2", type="tool_call", content="search_kb")
        g.add_edge("n1", "n2")

        synced_count = adapter.sync_graph("s_100", g, root_cause_id="n2")
        assert synced_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
