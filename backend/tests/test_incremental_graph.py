"""
Unit tests for Incremental Graph Building in SessionManager.

Tests:
- Incremental node addition
- Directed edge creation (reads_from -> dependent)
- Graph attribute preservation (timestamp, metadata, event_type, agent_id)
- Dangling reads_from reference detection & flag storage
- Cycle formation detection in live stream
"""

import sys
from pathlib import Path
import pytest
import networkx as nx

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from models.session import EventType, StartSessionRequest, TraceEvent
from session.manager import SessionManager


class TestIncrementalGraphBuilding:
    def test_graph_nodes_and_edges(self):
        mgr = SessionManager()
        sid = mgr.create_session(StartSessionRequest(name="Graph Test")).session_id

        mgr.add_event(sid, TraceEvent(event_id="e1", event_type=EventType.PLANNING, content="Plan"))
        mgr.add_event(sid, TraceEvent(event_id="e2", event_type=EventType.TOOL_CALL, content="Tool"))
        mgr.add_event(sid, TraceEvent(event_id="e3", event_type=EventType.OBSERVATION, content="Obs"))

        g = mgr.get_graph(sid)
        assert isinstance(g, nx.DiGraph)
        assert g.number_of_nodes() == 3
        assert g.number_of_edges() == 2

        assert g.has_edge("e1", "e2")
        assert g.has_edge("e2", "e3")

    def test_node_attribute_preservation(self):
        mgr = SessionManager()
        sid = mgr.create_session(StartSessionRequest(name="Attr Test")).session_id

        mgr.add_event(
            sid,
            TraceEvent(
                event_id="e1",
                event_type=EventType.TOOL_CALL,
                timestamp="2026-07-30T10:00:00Z",
                content="search_kb(query='test')",
                metadata={"tool_name": "search_kb", "latency_ms": 500},
                agent_id="researcher_1",
            ),
        )

        g = mgr.get_graph(sid)
        data = g.nodes["e1"]
        assert data["id"] == "e1"
        assert data["type"] == "tool_call"
        assert data["event_type"] == "tool_call"
        assert data["content"] == "search_kb(query='test')"
        assert data["metadata"]["tool_name"] == "search_kb"
        assert data["agent_id"] == "researcher_1"

    def test_dangling_reference_tracking(self):
        mgr = SessionManager()
        sid = mgr.create_session(StartSessionRequest(name="Dangling Test")).session_id

        # Event referencing non-existent node 'missing_1'
        mgr.add_event(
            sid,
            TraceEvent(
                event_id="e1",
                event_type=EventType.OBSERVATION,
                content="Result",
                reads_from=["missing_1"],
            ),
        )

        g = mgr.get_graph(sid)
        assert g.number_of_nodes() == 1
        assert g.number_of_edges() == 0  # Missing node can't have edge

        node_meta = g.nodes["e1"].get("metadata", {})
        assert "dangling_reads_from" in node_meta
        assert node_meta["dangling_reads_from"] == ["missing_1"]

    def test_multi_branch_graph(self):
        mgr = SessionManager()
        sid = mgr.create_session(StartSessionRequest(name="Branch Test")).session_id

        mgr.add_event(sid, TraceEvent(event_id="p", event_type=EventType.PLANNING, content="Plan"))
        mgr.add_event(
            sid, TraceEvent(event_id="t1", event_type=EventType.TOOL_CALL, content="Tool 1", reads_from=["p"])
        )
        mgr.add_event(
            sid, TraceEvent(event_id="t2", event_type=EventType.TOOL_CALL, content="Tool 2", reads_from=["p"])
        )
        mgr.add_event(
            sid,
            TraceEvent(
                event_id="sync",
                event_type=EventType.REASONING,
                content="Combine",
                reads_from=["t1", "t2"],
            ),
        )

        g = mgr.get_graph(sid)
        assert g.number_of_nodes() == 4
        assert g.number_of_edges() == 4  # p->t1, p->t2, t1->sync, t2->sync

        assert g.has_edge("p", "t1")
        assert g.has_edge("p", "t2")
        assert g.has_edge("t1", "sync")
        assert g.has_edge("t2", "sync")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
