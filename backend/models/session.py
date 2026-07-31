"""
TraceMind Live Session Data Models.

Pydantic models for the live event-streaming system:
- EventType taxonomy and mapping to NodeType
- TraceEvent (single agent lifecycle event)
- SessionStatus state machine
- TraceSession (server-side session container)
- API request/response models
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator

try:
    from models.trace import (
        AnomalyFlag,
        DiagnosisResult,
        FullDiagnosisResponse,
        NodeType,
    )
except ImportError:
    from backend.models.trace import (
        AnomalyFlag,
        DiagnosisResult,
        FullDiagnosisResponse,
        NodeType,
    )


# ---------------------------------------------------------------------------
# Event Type Taxonomy
# ---------------------------------------------------------------------------
class EventType(str, Enum):
    """All possible agent lifecycle event types."""

    # Agent lifecycle
    PLANNING = "planning"
    LLM_CALL = "llm_call"
    LLM_RESPONSE = "llm_response"
    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"
    OBSERVATION = "observation"
    REASONING = "reasoning"
    DECISION = "decision"
    DELEGATION = "delegation"
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    ERROR = "error"
    FINAL_ANSWER = "final_answer"
    CUSTOM = "custom"


# ---------------------------------------------------------------------------
# EventType → NodeType mapping
# ---------------------------------------------------------------------------
EVENT_TYPE_TO_NODE_TYPE: Dict[EventType, NodeType] = {
    EventType.PLANNING: NodeType.PLAN,
    EventType.LLM_CALL: NodeType.TOOL_CALL,
    EventType.LLM_RESPONSE: NodeType.OBSERVATION,
    EventType.TOOL_CALL: NodeType.TOOL_CALL,
    EventType.TOOL_RESPONSE: NodeType.OBSERVATION,
    EventType.OBSERVATION: NodeType.OBSERVATION,
    EventType.REASONING: NodeType.REASONING,
    EventType.DECISION: NodeType.DECISION,
    EventType.DELEGATION: NodeType.DELEGATION,
    EventType.MEMORY_READ: NodeType.OBSERVATION,
    EventType.MEMORY_WRITE: NodeType.OBSERVATION,
    EventType.ERROR: NodeType.OBSERVATION,
    EventType.FINAL_ANSWER: NodeType.FINAL_ANSWER,
    EventType.CUSTOM: NodeType.OBSERVATION,
}


def map_event_type_to_node_type(event_type: EventType) -> NodeType:
    """Map an EventType to the corresponding NodeType for graph construction."""
    return EVENT_TYPE_TO_NODE_TYPE.get(event_type, NodeType.OBSERVATION)


# ---------------------------------------------------------------------------
# Session Status State Machine
# ---------------------------------------------------------------------------
class SessionStatus(str, Enum):
    """Session lifecycle states."""

    CREATED = "created"  # Session allocated, no events yet
    RUNNING = "running"  # At least one event received
    COMPLETING = "completing"  # finish() called, diagnosis running
    COMPLETED = "completed"  # Diagnosis complete, session frozen
    FAILED = "failed"  # Session errored out
    EXPIRED = "expired"  # TTL exceeded without finish()


# Valid state transitions
VALID_TRANSITIONS: Dict[SessionStatus, set] = {
    SessionStatus.CREATED: {SessionStatus.RUNNING, SessionStatus.FAILED, SessionStatus.EXPIRED},
    SessionStatus.RUNNING: {
        SessionStatus.COMPLETING,
        SessionStatus.FAILED,
        SessionStatus.EXPIRED,
    },
    SessionStatus.COMPLETING: {
        SessionStatus.COMPLETED,
        SessionStatus.FAILED,
    },
    SessionStatus.COMPLETED: set(),  # Terminal
    SessionStatus.FAILED: set(),  # Terminal
    SessionStatus.EXPIRED: set(),  # Terminal
}

# States that accept new events
ACCEPTING_STATES = {SessionStatus.CREATED, SessionStatus.RUNNING, SessionStatus.COMPLETING}

# Terminal states
TERMINAL_STATES = {SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.EXPIRED}


def is_valid_transition(from_status: SessionStatus, to_status: SessionStatus) -> bool:
    """Check if a state transition is valid."""
    return to_status in VALID_TRANSITIONS.get(from_status, set())


# ---------------------------------------------------------------------------
# TraceEvent
# ---------------------------------------------------------------------------
class TraceEvent(BaseModel):
    """A single agent lifecycle event emitted by the SDK."""

    event_id: str = ""  # Client-generated or server-assigned
    event_type: EventType
    timestamp: str = ""  # ISO-8601, client-provided or auto-generated
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    reads_from: Optional[List[str]] = None  # None = auto-link to previous
    parent_event_id: Optional[str] = None  # Hierarchical parent
    agent_id: Optional[str] = None  # Sub-agent identifier
    sequence_number: Optional[int] = None  # Client-side ordering

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Event content must not be empty")
        return v

    @field_validator("content")
    @classmethod
    def content_size_limit(cls, v: str) -> str:
        max_size = 102400  # 100KB
        if len(v.encode("utf-8")) > max_size:
            raise ValueError(f"Event content exceeds {max_size} byte limit")
        return v


# ---------------------------------------------------------------------------
# TraceSession
# ---------------------------------------------------------------------------
class TraceSession(BaseModel):
    """A live trace session with its full state."""

    session_id: str
    name: str
    description: str = ""
    status: SessionStatus = SessionStatus.CREATED
    created_at: str  # ISO-8601
    updated_at: str  # ISO-8601, updated on every event
    finished_at: Optional[str] = None  # Set on finish()
    events: List[TraceEvent] = Field(default_factory=list)
    event_count: int = 0
    agent_ids: List[str] = Field(default_factory=list)
    tags: Dict[str, str] = Field(default_factory=dict)
    diagnosis: Optional[DiagnosisResult] = None
    full_diagnosis: Optional[FullDiagnosisResponse] = None
    error: Optional[str] = None
    ttl_seconds: int = 3600  # Default 1 hour

    def can_accept_events(self) -> bool:
        """Check if session is in a state that accepts new events."""
        return self.status in ACCEPTING_STATES

    def is_terminal(self) -> bool:
        """Check if session is in a terminal state."""
        return self.status in TERMINAL_STATES

    def transition_to(self, new_status: SessionStatus) -> None:
        """Transition to a new status, raising ValueError if invalid."""
        if not is_valid_transition(self.status, new_status):
            raise ValueError(
                f"Invalid state transition: {self.status.value} → {new_status.value}"
            )
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Session Summary (lightweight listing model)
# ---------------------------------------------------------------------------
class SessionSummary(BaseModel):
    """Lightweight session info for listing."""

    session_id: str
    name: str
    description: str = ""
    status: SessionStatus
    event_count: int = 0
    created_at: str
    updated_at: str
    agent_ids: List[str] = Field(default_factory=list)
    tags: Dict[str, str] = Field(default_factory=dict)

    @classmethod
    def from_session(cls, session: TraceSession) -> "SessionSummary":
        """Create a summary from a full session."""
        return cls(
            session_id=session.session_id,
            name=session.name,
            description=session.description,
            status=session.status,
            event_count=session.event_count,
            created_at=session.created_at,
            updated_at=session.updated_at,
            agent_ids=session.agent_ids,
            tags=session.tags,
        )


# ---------------------------------------------------------------------------
# API Request / Response Models
# ---------------------------------------------------------------------------
class StartSessionRequest(BaseModel):
    """Request body for POST /sessions/start."""

    name: str
    description: str = ""
    tags: Dict[str, str] = Field(default_factory=dict)
    ttl_seconds: int = 3600

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Session name must not be empty")
        return v.strip()

    @field_validator("name")
    @classmethod
    def name_length_limit(cls, v: str) -> str:
        if len(v) > 256:
            raise ValueError("Session name must be 256 characters or fewer")
        return v


class StartSessionResponse(BaseModel):
    """Response body for POST /sessions/start."""

    session_id: str
    status: SessionStatus
    ws_url: str
    created_at: str


class IngestEventRequest(BaseModel):
    """Request body for POST /sessions/{id}/events."""

    event: TraceEvent


class IngestBatchRequest(BaseModel):
    """Request body for POST /sessions/{id}/events/batch."""

    events: List[TraceEvent]

    @field_validator("events")
    @classmethod
    def batch_size_limit(cls, v: List[TraceEvent]) -> List[TraceEvent]:
        if len(v) > 100:
            raise ValueError("Batch size must not exceed 100 events")
        if len(v) == 0:
            raise ValueError("Batch must contain at least one event")
        return v


class IngestEventResponse(BaseModel):
    """Response body for event ingestion."""

    session_id: str
    event_id: str
    node_id: str  # Graph node ID created
    event_count: int
    status: SessionStatus


class FinishSessionRequest(BaseModel):
    """Request body for POST /sessions/{id}/finish."""

    trigger_diagnosis: bool = True
    failure_hint: Optional[str] = None


class FinishSessionResponse(BaseModel):
    """Response body for POST /sessions/{id}/finish."""

    session_id: str
    status: SessionStatus
    diagnosis: Optional[FullDiagnosisResponse] = None


# ---------------------------------------------------------------------------
# Error response model
# ---------------------------------------------------------------------------
class ErrorCode(str, Enum):
    """Structured error codes for the session API."""

    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SESSION_NOT_ACCEPTING = "SESSION_NOT_ACCEPTING"
    SESSION_EMPTY = "SESSION_EMPTY"
    EVENT_VALIDATION_FAILED = "EVENT_VALIDATION_FAILED"
    EVENT_DUPLICATE_ID = "EVENT_DUPLICATE_ID"
    EVENT_DANGLING_REFERENCE = "EVENT_DANGLING_REFERENCE"
    BATCH_TOO_LARGE = "BATCH_TOO_LARGE"
    DIAGNOSIS_FAILED = "DIAGNOSIS_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    WS_SESSION_NOT_FOUND = "WS_SESSION_NOT_FOUND"


class ErrorDetail(BaseModel):
    """Structured error response body."""

    code: ErrorCode
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------
class PaginatedSessions(BaseModel):
    """Paginated session listing response."""

    items: List[SessionSummary]
    total: int
    limit: int
    offset: int
    has_more: bool


class PaginatedEvents(BaseModel):
    """Paginated event listing response."""

    items: List[TraceEvent]
    total: int
    limit: int
    offset: int
    has_more: bool


# ---------------------------------------------------------------------------
# WebSocket message types
# ---------------------------------------------------------------------------
class WSMessageType(str, Enum):
    """WebSocket message types (server → client)."""

    CONNECTED = "connected"
    NODE_ADDED = "node_added"
    EDGE_ADDED = "edge_added"
    ANOMALY_DETECTED = "anomaly_detected"
    SESSION_STATUS = "session_status"
    DIAGNOSIS_COMPLETE = "diagnosis_complete"
    PING = "ping"
    ERROR = "error"
    SNAPSHOT = "snapshot"
