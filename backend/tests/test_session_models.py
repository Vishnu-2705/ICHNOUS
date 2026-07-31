"""
Unit tests for TraceMind live session data models.

Tests:
- EventType enum values and completeness
- EventType → NodeType mapping coverage
- SessionStatus state machine transitions
- TraceEvent validation (content, size limits)
- TraceSession lifecycle helpers (can_accept_events, is_terminal, transition_to)
- SessionSummary.from_session()
- API request/response model validation
- InMemoryStorage CRUD and pagination
"""

import sys
from pathlib import Path

import pytest

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from models.session import (
    ACCEPTING_STATES,
    EVENT_TYPE_TO_NODE_TYPE,
    TERMINAL_STATES,
    VALID_TRANSITIONS,
    ErrorCode,
    EventType,
    FinishSessionRequest,
    IngestBatchRequest,
    IngestEventRequest,
    IngestEventResponse,
    PaginatedSessions,
    SessionStatus,
    SessionSummary,
    StartSessionRequest,
    StartSessionResponse,
    TraceEvent,
    TraceSession,
    WSMessageType,
    is_valid_transition,
    map_event_type_to_node_type,
)
from models.trace import NodeType
from session.storage import InMemoryStorage


# ---------------------------------------------------------------------------
# EventType tests
# ---------------------------------------------------------------------------
class TestEventType:
    def test_all_14_event_types(self):
        """EventType enum must contain exactly 14 values."""
        assert len(EventType) == 14

    def test_event_type_values(self):
        """All expected event type string values exist."""
        expected = {
            "planning", "llm_call", "llm_response", "tool_call",
            "tool_response", "observation", "reasoning", "decision",
            "delegation", "memory_read", "memory_write", "error",
            "final_answer", "custom",
        }
        actual = {e.value for e in EventType}
        assert actual == expected

    def test_every_event_type_has_node_mapping(self):
        """Every EventType must have a corresponding NodeType mapping."""
        for et in EventType:
            result = map_event_type_to_node_type(et)
            assert isinstance(result, NodeType), (
                f"EventType.{et.name} mapped to {type(result)}, expected NodeType"
            )

    def test_specific_mappings(self):
        """Verify key EventType → NodeType mappings."""
        assert map_event_type_to_node_type(EventType.PLANNING) == NodeType.PLAN
        assert map_event_type_to_node_type(EventType.TOOL_CALL) == NodeType.TOOL_CALL
        assert map_event_type_to_node_type(EventType.TOOL_RESPONSE) == NodeType.OBSERVATION
        assert map_event_type_to_node_type(EventType.REASONING) == NodeType.REASONING
        assert map_event_type_to_node_type(EventType.DECISION) == NodeType.DECISION
        assert map_event_type_to_node_type(EventType.DELEGATION) == NodeType.DELEGATION
        assert map_event_type_to_node_type(EventType.FINAL_ANSWER) == NodeType.FINAL_ANSWER
        assert map_event_type_to_node_type(EventType.ERROR) == NodeType.OBSERVATION
        assert map_event_type_to_node_type(EventType.CUSTOM) == NodeType.OBSERVATION

    def test_mapping_dict_covers_all_types(self):
        """EVENT_TYPE_TO_NODE_TYPE dict must cover every EventType."""
        for et in EventType:
            assert et in EVENT_TYPE_TO_NODE_TYPE, f"Missing mapping for {et}"


# ---------------------------------------------------------------------------
# SessionStatus state machine tests
# ---------------------------------------------------------------------------
class TestSessionStatus:
    def test_all_6_statuses(self):
        assert len(SessionStatus) == 6

    def test_status_values(self):
        expected = {"created", "running", "completing", "completed", "failed", "expired"}
        actual = {s.value for s in SessionStatus}
        assert actual == expected

    def test_terminal_states(self):
        assert TERMINAL_STATES == {
            SessionStatus.COMPLETED,
            SessionStatus.FAILED,
            SessionStatus.EXPIRED,
        }

    def test_accepting_states(self):
        assert ACCEPTING_STATES == {
            SessionStatus.CREATED,
            SessionStatus.RUNNING,
            SessionStatus.COMPLETING,
        }

    def test_valid_transition_created_to_running(self):
        assert is_valid_transition(SessionStatus.CREATED, SessionStatus.RUNNING)

    def test_valid_transition_running_to_completing(self):
        assert is_valid_transition(SessionStatus.RUNNING, SessionStatus.COMPLETING)

    def test_valid_transition_completing_to_completed(self):
        assert is_valid_transition(SessionStatus.COMPLETING, SessionStatus.COMPLETED)

    def test_invalid_transition_completed_to_running(self):
        assert not is_valid_transition(SessionStatus.COMPLETED, SessionStatus.RUNNING)

    def test_invalid_transition_failed_to_running(self):
        assert not is_valid_transition(SessionStatus.FAILED, SessionStatus.RUNNING)

    def test_any_state_can_fail(self):
        """CREATED, RUNNING, COMPLETING can all transition to FAILED."""
        for s in [SessionStatus.CREATED, SessionStatus.RUNNING, SessionStatus.COMPLETING]:
            assert is_valid_transition(s, SessionStatus.FAILED)

    def test_terminal_states_have_no_transitions(self):
        for s in TERMINAL_STATES:
            assert VALID_TRANSITIONS[s] == set()


# ---------------------------------------------------------------------------
# TraceEvent tests
# ---------------------------------------------------------------------------
class TestTraceEvent:
    def test_basic_event_creation(self):
        event = TraceEvent(
            event_id="evt_1",
            event_type=EventType.PLANNING,
            timestamp="2026-07-30T10:00:00Z",
            content="Planning step",
        )
        assert event.event_id == "evt_1"
        assert event.event_type == EventType.PLANNING
        assert event.content == "Planning step"
        assert event.metadata == {}
        assert event.reads_from is None
        assert event.parent_event_id is None
        assert event.agent_id is None

    def test_event_with_auto_link_none(self):
        """reads_from=None means auto-link to previous."""
        event = TraceEvent(
            event_type=EventType.TOOL_CALL,
            content="Calling tool",
        )
        assert event.reads_from is None

    def test_event_with_explicit_reads_from(self):
        event = TraceEvent(
            event_type=EventType.OBSERVATION,
            content="Got result",
            reads_from=["evt_1", "evt_2"],
        )
        assert event.reads_from == ["evt_1", "evt_2"]

    def test_event_with_empty_reads_from(self):
        """reads_from=[] means root event with no dependencies."""
        event = TraceEvent(
            event_type=EventType.PLANNING,
            content="Root event",
            reads_from=[],
        )
        assert event.reads_from == []

    def test_empty_content_rejected(self):
        with pytest.raises(Exception):
            TraceEvent(
                event_type=EventType.PLANNING,
                content="",
            )

    def test_whitespace_content_rejected(self):
        with pytest.raises(Exception):
            TraceEvent(
                event_type=EventType.PLANNING,
                content="   ",
            )

    def test_content_size_limit(self):
        """Content exceeding 100KB should be rejected."""
        large_content = "x" * 102401
        with pytest.raises(Exception):
            TraceEvent(
                event_type=EventType.PLANNING,
                content=large_content,
            )

    def test_content_within_limit(self):
        content = "x" * 102400  # Exactly 100KB
        event = TraceEvent(
            event_type=EventType.PLANNING,
            content=content,
        )
        assert len(event.content) == 102400

    def test_event_with_metadata(self):
        event = TraceEvent(
            event_type=EventType.TOOL_CALL,
            content="search_kb()",
            metadata={"tool_name": "search_kb", "latency_ms": 450},
        )
        assert event.metadata["tool_name"] == "search_kb"
        assert event.metadata["latency_ms"] == 450

    def test_event_with_agent_id(self):
        event = TraceEvent(
            event_type=EventType.DELEGATION,
            content="Delegating to ResearchAgent",
            agent_id="research_agent_1",
        )
        assert event.agent_id == "research_agent_1"


# ---------------------------------------------------------------------------
# TraceSession tests
# ---------------------------------------------------------------------------
class TestTraceSession:
    def _make_session(self, **kwargs) -> TraceSession:
        defaults = {
            "session_id": "test-session-1",
            "name": "Test Session",
            "created_at": "2026-07-30T10:00:00Z",
            "updated_at": "2026-07-30T10:00:00Z",
        }
        defaults.update(kwargs)
        return TraceSession(**defaults)

    def test_default_status_is_created(self):
        session = self._make_session()
        assert session.status == SessionStatus.CREATED

    def test_can_accept_events_in_created(self):
        session = self._make_session(status=SessionStatus.CREATED)
        assert session.can_accept_events()

    def test_can_accept_events_in_running(self):
        session = self._make_session(status=SessionStatus.RUNNING)
        assert session.can_accept_events()

    def test_can_accept_events_in_completing(self):
        session = self._make_session(status=SessionStatus.COMPLETING)
        assert session.can_accept_events()

    def test_cannot_accept_events_in_completed(self):
        session = self._make_session(status=SessionStatus.COMPLETED)
        assert not session.can_accept_events()

    def test_cannot_accept_events_in_failed(self):
        session = self._make_session(status=SessionStatus.FAILED)
        assert not session.can_accept_events()

    def test_is_terminal_completed(self):
        session = self._make_session(status=SessionStatus.COMPLETED)
        assert session.is_terminal()

    def test_is_not_terminal_running(self):
        session = self._make_session(status=SessionStatus.RUNNING)
        assert not session.is_terminal()

    def test_transition_created_to_running(self):
        session = self._make_session()
        session.transition_to(SessionStatus.RUNNING)
        assert session.status == SessionStatus.RUNNING

    def test_transition_running_to_completing(self):
        session = self._make_session(status=SessionStatus.RUNNING)
        session.transition_to(SessionStatus.COMPLETING)
        assert session.status == SessionStatus.COMPLETING

    def test_invalid_transition_raises(self):
        session = self._make_session(status=SessionStatus.COMPLETED)
        with pytest.raises(ValueError, match="Invalid state transition"):
            session.transition_to(SessionStatus.RUNNING)

    def test_transition_updates_timestamp(self):
        session = self._make_session()
        old_updated = session.updated_at
        session.transition_to(SessionStatus.RUNNING)
        assert session.updated_at != old_updated

    def test_session_with_tags(self):
        session = self._make_session(tags={"env": "staging", "version": "1.0"})
        assert session.tags["env"] == "staging"

    def test_default_ttl(self):
        session = self._make_session()
        assert session.ttl_seconds == 3600


# ---------------------------------------------------------------------------
# SessionSummary tests
# ---------------------------------------------------------------------------
class TestSessionSummary:
    def test_from_session(self):
        session = TraceSession(
            session_id="s-1",
            name="Test",
            description="A test session",
            status=SessionStatus.RUNNING,
            event_count=5,
            created_at="2026-07-30T10:00:00Z",
            updated_at="2026-07-30T10:01:00Z",
            agent_ids=["agent_a"],
            tags={"team": "infra"},
        )
        summary = SessionSummary.from_session(session)
        assert summary.session_id == "s-1"
        assert summary.name == "Test"
        assert summary.status == SessionStatus.RUNNING
        assert summary.event_count == 5
        assert summary.agent_ids == ["agent_a"]
        assert summary.tags == {"team": "infra"}


# ---------------------------------------------------------------------------
# API Request Model tests
# ---------------------------------------------------------------------------
class TestAPIModels:
    def test_start_session_request_valid(self):
        req = StartSessionRequest(name="My Agent Run")
        assert req.name == "My Agent Run"
        assert req.description == ""
        assert req.tags == {}
        assert req.ttl_seconds == 3600

    def test_start_session_request_empty_name_rejected(self):
        with pytest.raises(Exception):
            StartSessionRequest(name="")

    def test_start_session_request_long_name_rejected(self):
        with pytest.raises(Exception):
            StartSessionRequest(name="x" * 257)

    def test_ingest_batch_empty_rejected(self):
        with pytest.raises(Exception):
            IngestBatchRequest(events=[])

    def test_ingest_batch_over_100_rejected(self):
        events = [
            TraceEvent(event_type=EventType.PLANNING, content=f"Event {i}")
            for i in range(101)
        ]
        with pytest.raises(Exception):
            IngestBatchRequest(events=events)

    def test_ingest_batch_100_accepted(self):
        events = [
            TraceEvent(event_type=EventType.PLANNING, content=f"Event {i}")
            for i in range(100)
        ]
        batch = IngestBatchRequest(events=events)
        assert len(batch.events) == 100

    def test_finish_session_defaults(self):
        req = FinishSessionRequest()
        assert req.trigger_diagnosis is True
        assert req.failure_hint is None


# ---------------------------------------------------------------------------
# InMemoryStorage tests
# ---------------------------------------------------------------------------
class TestInMemoryStorage:
    def _make_session(self, session_id: str, **kwargs) -> TraceSession:
        defaults = {
            "session_id": session_id,
            "name": f"Session {session_id}",
            "created_at": "2026-07-30T10:00:00Z",
            "updated_at": "2026-07-30T10:00:00Z",
        }
        defaults.update(kwargs)
        return TraceSession(**defaults)

    def test_create_and_get(self):
        storage = InMemoryStorage()
        session = self._make_session("s-1")
        storage.create_session(session)
        retrieved = storage.get_session("s-1")
        assert retrieved is not None
        assert retrieved.session_id == "s-1"

    def test_create_duplicate_raises(self):
        storage = InMemoryStorage()
        session = self._make_session("s-1")
        storage.create_session(session)
        with pytest.raises(ValueError, match="already exists"):
            storage.create_session(session)

    def test_get_nonexistent_returns_none(self):
        storage = InMemoryStorage()
        assert storage.get_session("nonexistent") is None

    def test_update_session(self):
        storage = InMemoryStorage()
        session = self._make_session("s-1")
        storage.create_session(session)
        session.status = SessionStatus.RUNNING
        session.event_count = 5
        storage.update_session(session)
        retrieved = storage.get_session("s-1")
        assert retrieved.status == SessionStatus.RUNNING
        assert retrieved.event_count == 5

    def test_update_nonexistent_raises(self):
        storage = InMemoryStorage()
        session = self._make_session("s-1")
        with pytest.raises(ValueError, match="not found"):
            storage.update_session(session)

    def test_delete_session(self):
        storage = InMemoryStorage()
        session = self._make_session("s-1")
        storage.create_session(session)
        assert storage.delete_session("s-1") is True
        assert storage.get_session("s-1") is None

    def test_delete_nonexistent_returns_false(self):
        storage = InMemoryStorage()
        assert storage.delete_session("nonexistent") is False

    def test_session_exists(self):
        storage = InMemoryStorage()
        storage.create_session(self._make_session("s-1"))
        assert storage.session_exists("s-1")
        assert not storage.session_exists("s-2")

    def test_list_sessions_all(self):
        storage = InMemoryStorage()
        for i in range(5):
            storage.create_session(
                self._make_session(f"s-{i}", created_at=f"2026-07-30T10:0{i}:00Z")
            )
        items, total = storage.list_sessions()
        assert total == 5
        assert len(items) == 5

    def test_list_sessions_with_status_filter(self):
        storage = InMemoryStorage()
        storage.create_session(self._make_session("s-1", status=SessionStatus.RUNNING))
        storage.create_session(self._make_session("s-2", status=SessionStatus.COMPLETED))
        storage.create_session(self._make_session("s-3", status=SessionStatus.RUNNING))
        items, total = storage.list_sessions(status=SessionStatus.RUNNING)
        assert total == 2
        assert all(s.status == SessionStatus.RUNNING for s in items)

    def test_list_sessions_pagination(self):
        storage = InMemoryStorage()
        for i in range(10):
            storage.create_session(
                self._make_session(f"s-{i}", created_at=f"2026-07-30T10:{i:02d}:00Z")
            )
        items, total = storage.list_sessions(limit=3, offset=0)
        assert total == 10
        assert len(items) == 3

        items2, total2 = storage.list_sessions(limit=3, offset=3)
        assert total2 == 10
        assert len(items2) == 3

    def test_count_by_status(self):
        storage = InMemoryStorage()
        storage.create_session(self._make_session("s-1", status=SessionStatus.RUNNING))
        storage.create_session(self._make_session("s-2", status=SessionStatus.RUNNING))
        storage.create_session(self._make_session("s-3", status=SessionStatus.COMPLETED))
        assert storage.count_by_status(SessionStatus.RUNNING) == 2
        assert storage.count_by_status(SessionStatus.COMPLETED) == 1
        assert storage.count_by_status(SessionStatus.FAILED) == 0

    def test_count_total(self):
        storage = InMemoryStorage()
        assert storage.count_total() == 0
        storage.create_session(self._make_session("s-1"))
        storage.create_session(self._make_session("s-2"))
        assert storage.count_total() == 2

    def test_list_active_session_ids(self):
        storage = InMemoryStorage()
        storage.create_session(self._make_session("s-1", status=SessionStatus.RUNNING))
        storage.create_session(self._make_session("s-2", status=SessionStatus.COMPLETED))
        storage.create_session(self._make_session("s-3", status=SessionStatus.CREATED))
        active = storage.list_active_session_ids()
        assert set(active) == {"s-1", "s-3"}

    def test_clear(self):
        storage = InMemoryStorage()
        storage.create_session(self._make_session("s-1"))
        storage.create_session(self._make_session("s-2"))
        storage.clear()
        assert storage.count_total() == 0


# ---------------------------------------------------------------------------
# ErrorCode and WSMessageType completeness
# ---------------------------------------------------------------------------
class TestEnumCompleteness:
    def test_error_codes(self):
        assert len(ErrorCode) == 10

    def test_ws_message_types(self):
        assert len(WSMessageType) == 9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
