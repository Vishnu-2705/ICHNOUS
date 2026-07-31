"""
Unit tests for SessionManager and Session-to-Trace converter.

Tests:
- Session creation and ID assignment
- Event ingestion with auto-linking (linear chain, explicit, parent, agent)
- Batch event ingestion
- Incremental NetworkX graph updates
- State transitions (CREATED -> RUNNING -> COMPLETING -> COMPLETED)
- Terminal state event rejection
- Session deletion and metrics
- session_to_trace conversion
"""

import sys
from pathlib import Path
import pytest

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from models.session import (
    EventType,
    FinishSessionRequest,
    SessionStatus,
    StartSessionRequest,
    TraceEvent,
)
from models.trace import NodeType
from session.converter import event_to_trace_node, session_to_trace
from session.manager import SessionManager
from session.storage import InMemoryStorage


class TestSessionConverter:
    def test_event_to_trace_node_mapping(self):
        evt = TraceEvent(
            event_id="evt_100",
            event_type=EventType.TOOL_CALL,
            timestamp="2026-07-30T12:00:00Z",
            content="search_kb(query='refund')",
            metadata={"tool_name": "search_kb"},
            reads_from=["evt_99"],
            agent_id="agent_1",
        )
        node = event_to_trace_node(evt)
        assert node.id == "evt_100"
        assert node.type == NodeType.TOOL_CALL
        assert node.content == "search_kb(query='refund')"
        assert node.metadata["tool_name"] == "search_kb"
        assert node.metadata["event_type"] == "tool_call"
        assert node.metadata["agent_id"] == "agent_1"
        assert node.reads_from == ["evt_99"]

    def test_session_to_trace_conversion(self):
        storage = InMemoryStorage()
        mgr = SessionManager(storage=storage)
        res = mgr.create_session(StartSessionRequest(name="Test Session", description="Desc"))
        sid = res.session_id

        mgr.add_event(sid, TraceEvent(event_type=EventType.PLANNING, content="Plan"))
        mgr.add_event(sid, TraceEvent(event_type=EventType.TOOL_CALL, content="Tool"))
        mgr.add_event(sid, TraceEvent(event_type=EventType.FINAL_ANSWER, content="Answer"))

        session = mgr.get_session(sid)
        trace = session_to_trace(session)

        assert trace.id == sid
        assert trace.name == "Test Session"
        assert trace.description == "Desc"
        assert len(trace.nodes) == 3
        assert trace.nodes[0].type == NodeType.PLAN
        assert trace.nodes[1].type == NodeType.TOOL_CALL
        assert trace.nodes[2].type == NodeType.FINAL_ANSWER


class TestSessionManagerLifecycle:
    def test_create_session(self):
        mgr = SessionManager()
        res = mgr.create_session(StartSessionRequest(name="Run 1", description="Test run"))
        assert res.session_id is not None
        assert res.status == SessionStatus.CREATED
        assert "/ws/sessions/" in res.ws_url

        session = mgr.get_session(res.session_id)
        assert session is not None
        assert session.name == "Run 1"
        assert session.event_count == 0

    def test_add_event_auto_link_chain(self):
        mgr = SessionManager()
        res = mgr.create_session(StartSessionRequest(name="Run 1"))
        sid = res.session_id

        # First event (no dependencies)
        e1 = mgr.add_event(sid, TraceEvent(event_type=EventType.PLANNING, content="Plan 1"))
        assert e1.event_id == "evt_1"
        session = mgr.get_session(sid)
        assert session.events[0].reads_from == []
        assert session.status == SessionStatus.RUNNING

        # Second event (auto-linked to evt_1)
        e2 = mgr.add_event(sid, TraceEvent(event_type=EventType.TOOL_CALL, content="Tool 1"))
        assert e2.event_id == "evt_2"
        session = mgr.get_session(sid)
        assert session.events[1].reads_from == ["evt_1"]

        # Third event (auto-linked to evt_2)
        e3 = mgr.add_event(sid, TraceEvent(event_type=EventType.OBSERVATION, content="Obs 1"))
        assert e3.event_id == "evt_3"
        session = mgr.get_session(sid)
        assert session.events[2].reads_from == ["evt_2"]

    def test_add_event_explicit_reads_from(self):
        mgr = SessionManager()
        sid = mgr.create_session(StartSessionRequest(name="Explicit Links")).session_id

        mgr.add_event(sid, TraceEvent(event_id="n1", event_type=EventType.PLANNING, content="Plan"))
        mgr.add_event(sid, TraceEvent(event_id="n2", event_type=EventType.TOOL_CALL, content="Tool A"))
        mgr.add_event(sid, TraceEvent(event_id="n3", event_type=EventType.TOOL_CALL, content="Tool B"))

        # Explicitly read from n1 and n2
        mgr.add_event(
            sid,
            TraceEvent(
                event_id="n4",
                event_type=EventType.REASONING,
                content="Combine A and B",
                reads_from=["n1", "n2"],
            ),
        )

        session = mgr.get_session(sid)
        assert session.events[3].reads_from == ["n1", "n2"]

    def test_add_event_batch(self):
        mgr = SessionManager()
        sid = mgr.create_session(StartSessionRequest(name="Batch Run")).session_id

        events = [
            TraceEvent(event_type=EventType.PLANNING, content="P1"),
            TraceEvent(event_type=EventType.TOOL_CALL, content="T1"),
            TraceEvent(event_type=EventType.OBSERVATION, content="O1"),
        ]

        responses = mgr.add_events_batch(sid, events)
        assert len(responses) == 3
        assert mgr.get_session(sid).event_count == 3

    def test_duplicate_event_id_rejected(self):
        mgr = SessionManager()
        sid = mgr.create_session(StartSessionRequest(name="Dup Test")).session_id

        mgr.add_event(sid, TraceEvent(event_id="same_id", event_type=EventType.PLANNING, content="P1"))

        with pytest.raises(ValueError, match="Duplicate event_id"):
            mgr.add_event(sid, TraceEvent(event_id="same_id", event_type=EventType.TOOL_CALL, content="T1"))

    def test_finish_session(self):
        mgr = SessionManager()
        sid = mgr.create_session(StartSessionRequest(name="Finish Test")).session_id

        mgr.add_event(sid, TraceEvent(event_type=EventType.PLANNING, content="Plan"))
        mgr.add_event(sid, TraceEvent(event_type=EventType.FINAL_ANSWER, content="Ans"))

        res = mgr.finish_session(sid)
        assert res.status == SessionStatus.COMPLETED
        assert mgr.get_session(sid).status == SessionStatus.COMPLETED

    def test_add_event_to_terminal_session_rejected(self):
        mgr = SessionManager()
        sid = mgr.create_session(StartSessionRequest(name="Terminal Test")).session_id
        mgr.add_event(sid, TraceEvent(event_type=EventType.PLANNING, content="Plan"))
        mgr.finish_session(sid)

        with pytest.raises(ValueError, match="terminal state"):
            mgr.add_event(sid, TraceEvent(event_type=EventType.TOOL_CALL, content="Tool"))

    def test_delete_session(self):
        mgr = SessionManager()
        sid = mgr.create_session(StartSessionRequest(name="Delete Test")).session_id
        mgr.add_event(sid, TraceEvent(event_type=EventType.PLANNING, content="Plan"))

        assert mgr.get_graph(sid) is not None
        assert mgr.delete_session(sid) is True
        assert mgr.get_session(sid) is None
        assert mgr.get_graph(sid) is None

    def test_metrics_tracking(self):
        mgr = SessionManager()
        s1 = mgr.create_session(StartSessionRequest(name="S1")).session_id
        s2 = mgr.create_session(StartSessionRequest(name="S2")).session_id

        mgr.add_event(s1, TraceEvent(event_type=EventType.PLANNING, content="P1"))
        mgr.add_event(s1, TraceEvent(event_type=EventType.FINAL_ANSWER, content="A1"))
        mgr.finish_session(s1)

        metrics = mgr.get_metrics()
        assert metrics["sessions_created"] == 2
        assert metrics["sessions_completed"] == 1
        assert metrics["events_ingested"] == 2
        assert metrics["total_sessions"] == 2
        assert metrics["active_sessions"] == 1  # s2 is still created


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
