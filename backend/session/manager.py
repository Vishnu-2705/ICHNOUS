"""
Session Manager Service for TraceMind.

Central orchestrator for live session management:
- Thread-safe session storage and state transitions
- Incremental NetworkX graph construction per session
- Automatic reads_from dependency linking
- Event validation, indexing, and sequence ordering
- Integration with StorageBackend
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import threading
from typing import Any, Dict, List, Optional, Tuple, Set
import uuid

import networkx as nx

try:
    from models.session import (
        ACCEPTING_STATES,
        TERMINAL_STATES,
        ErrorCode,
        EventType,
        FinishSessionRequest,
        FinishSessionResponse,
        IngestEventResponse,
        SessionStatus,
        SessionSummary,
        StartSessionRequest,
        StartSessionResponse,
        TraceEvent,
        TraceSession,
        map_event_type_to_node_type,
    )
    from models.trace import FullDiagnosisResponse
    from session.converter import event_to_trace_node, session_to_trace
    from session.diagnosis import diagnose_session
    from session.storage import InMemoryStorage, StorageBackend
except ImportError:
    from backend.models.session import (
        ACCEPTING_STATES,
        TERMINAL_STATES,
        ErrorCode,
        EventType,
        FinishSessionRequest,
        FinishSessionResponse,
        IngestEventResponse,
        SessionStatus,
        SessionSummary,
        StartSessionRequest,
        StartSessionResponse,
        TraceEvent,
        TraceSession,
        map_event_type_to_node_type,
    )
    from backend.models.trace import FullDiagnosisResponse
    from backend.session.converter import event_to_trace_node, session_to_trace
    from backend.session.diagnosis import diagnose_session
    from backend.session.storage import InMemoryStorage, StorageBackend


class SessionManager:
    """
    Thread-safe manager for live agent trace sessions.
    
    Maintains:
    - Persistent sessions in a StorageBackend
    - In-memory networkx.DiGraph instances built incrementally per session
    - Per-session lock table for fine-grained concurrency control
    - Event auto-linking and sequence generation
    """

    def __init__(self, storage: Optional[StorageBackend] = None, ws_hub: Optional[Any] = None) -> None:
        self.storage = storage or InMemoryStorage()
        self.ws_hub = ws_hub
        self._graphs: Dict[str, nx.DiGraph] = {}
        self._session_locks: Dict[str, threading.RLock] = {}
        self._global_lock = threading.RLock()

        # Operational metrics tracking
        self._metrics = {
            "created": 0,
            "completed": 0,
            "failed": 0,
            "expired": 0,
            "events_ingested": 0,
        }

    def _broadcast(self, session_id: str, message: Dict[str, Any]) -> None:
        """Helper to broadcast WebSocket messages safely."""
        if not self.ws_hub:
            return
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.ws_hub.broadcast(session_id, message))
        except RuntimeError:
            pass

    def _get_session_lock(self, session_id: str) -> threading.RLock:
        """Retrieve or create a reentrant lock for a specific session."""
        with self._global_lock:
            if session_id not in self._session_locks:
                self._session_locks[session_id] = threading.RLock()
            return self._session_locks[session_id]

    def create_session(self, request: StartSessionRequest, session_id: Optional[str] = None) -> StartSessionResponse:
        """
        Create a new live trace session.
        """
        with self._global_lock:
            sid = session_id or str(uuid.uuid4())
            now_iso = datetime.now(timezone.utc).isoformat()

            session = TraceSession(
                session_id=sid,
                name=request.name,
                description=request.description,
                status=SessionStatus.CREATED,
                created_at=now_iso,
                updated_at=now_iso,
                tags=request.tags,
                ttl_seconds=request.ttl_seconds,
            )

            # Initialize empty graph for this session
            g = nx.DiGraph(session_id=sid, name=request.name)
            self._graphs[sid] = g

            # Persist session
            self.storage.create_session(session)
            self._metrics["created"] += 1

            ws_url = f"/ws/sessions/{sid}"
            return StartSessionResponse(
                session_id=sid,
                status=session.status,
                ws_url=ws_url,
                created_at=now_iso,
            )

    def _resolve_auto_link(self, session: TraceSession, event: TraceEvent) -> List[str]:
        """
        Determine reads_from dependency links for an incoming event.
        - If event.reads_from is explicitly provided (list), use it.
        - If event.reads_from is None:
          - If parent_event_id is present, link to parent.
          - If agent_id is present, link to previous event from same agent if available.
          - Otherwise, link to the most recent event in the session (linear chain).
          - If no previous events exist, return empty list [].
        """
        if event.reads_from is not None:
            return list(event.reads_from)

        if not session.events:
            return []

        if event.parent_event_id:
            return [event.parent_event_id]

        if event.agent_id:
            for prev in reversed(session.events):
                if prev.agent_id == event.agent_id:
                    return [prev.event_id]
            # Fallback for sub-agent: link to latest delegation event
            for prev in reversed(session.events):
                if prev.event_type == EventType.DELEGATION:
                    return [prev.event_id]

        # Standard fallback: link to immediate predecessor event
        return [session.events[-1].event_id]

    def add_event(self, session_id: str, event: TraceEvent) -> IngestEventResponse:
        """
        Add a single TraceEvent to a live session and incrementally update its graph.
        """
        lock = self._get_session_lock(session_id)
        with lock:
            session = self.storage.get_session(session_id)
            if not session:
                raise KeyError(f"Session '{session_id}' not found.")

            if not session.can_accept_events():
                raise ValueError(
                    f"Session '{session_id}' is in terminal state '{session.status.value}' and cannot accept events."
                )

            # Assign event ID if missing
            if not event.event_id:
                event.event_id = f"evt_{session.event_count + 1}"

            # Validate duplicate event IDs within session
            existing_ids = {e.event_id for e in session.events}
            if event.event_id in existing_ids:
                raise ValueError(f"Duplicate event_id '{event.event_id}' in session '{session_id}'.")

            # Set sequence number if missing
            if event.sequence_number is None:
                event.sequence_number = session.event_count + 1

            # Set timestamp if missing
            if not event.timestamp:
                event.timestamp = datetime.now(timezone.utc).isoformat()

            # Resolve auto-linking for reads_from
            resolved_reads_from = self._resolve_auto_link(session, event)
            event.reads_from = resolved_reads_from

            # Auto transition state CREATED -> RUNNING on first event
            if session.status == SessionStatus.CREATED:
                session.transition_to(SessionStatus.RUNNING)

            # Record event in session
            session.events.append(event)
            session.event_count = len(session.events)
            session.updated_at = datetime.now(timezone.utc).isoformat()

            if event.agent_id and event.agent_id not in session.agent_ids:
                session.agent_ids.append(event.agent_id)

            # Update incremental graph
            g = self._graphs.setdefault(session_id, nx.DiGraph(session_id=session_id))
            node_type = map_event_type_to_node_type(event.event_type)

            g.add_node(
                event.event_id,
                id=event.event_id,
                type=node_type.value,
                timestamp=event.timestamp,
                content=event.content,
                metadata=event.metadata,
                reads_from=event.reads_from,
                event_type=event.event_type.value,
                agent_id=event.agent_id,
            )

            # Add directed edges from dependency source to dependent node
            for upstream_id in event.reads_from:
                if g.has_node(upstream_id):
                    g.add_edge(upstream_id, event.event_id)
                else:
                    meta = g.nodes[event.event_id].setdefault("metadata", {})
                    dangling = meta.setdefault("dangling_reads_from", [])
                    if upstream_id not in dangling:
                        dangling.append(upstream_id)

            self.storage.update_session(session)
            self._metrics["events_ingested"] += 1

            # Broadcast node and edge additions via WebSocket
            node_payload = {
                "id": event.event_id,
                "type": node_type.value,
                "content": event.content,
                "metadata": event.metadata,
                "timestamp": event.timestamp,
                "highlight": "normal",
            }
            edges_payload = [
                {"source": src, "target": event.event_id, "from": src, "to": event.event_id, "highlight": "normal"}
                for src in event.reads_from
            ]
            self._broadcast(
                session_id,
                {
                    "type": "node_added",
                    "node": node_payload,
                    "edges": edges_payload,
                    "event_count": session.event_count,
                    "status": session.status.value,
                },
            )

            return IngestEventResponse(
                session_id=session_id,
                event_id=event.event_id,
                node_id=event.event_id,
                event_count=session.event_count,
                status=session.status,
            )

    def add_events_batch(self, session_id: str, events: List[TraceEvent]) -> List[IngestEventResponse]:
        """
        Add a batch of TraceEvents sequentially.
        """
        responses = []
        for event in events:
            res = self.add_event(session_id, event)
            responses.append(res)
        return responses

    def finish_session(
        self, session_id: str, request: Optional[FinishSessionRequest] = None
    ) -> FinishSessionResponse:
        """
        Mark a session as COMPLETING/COMPLETED and optionally trigger diagnosis.
        """
        lock = self._get_session_lock(session_id)
        with lock:
            session = self.storage.get_session(session_id)
            if not session:
                raise KeyError(f"Session '{session_id}' not found.")

            if session.is_terminal():
                return FinishSessionResponse(
                    session_id=session_id,
                    status=session.status,
                    diagnosis=session.full_diagnosis,
                )

            now_iso = datetime.now(timezone.utc).isoformat()
            trigger_diag = request.trigger_diagnosis if request is not None else True

            # Transition to COMPLETING then COMPLETED
            if session.status in (SessionStatus.CREATED, SessionStatus.RUNNING):
                session.transition_to(SessionStatus.COMPLETING)

            session.finished_at = now_iso

            # Run diagnosis if requested and events are present
            full_diag: Optional[FullDiagnosisResponse] = None
            if trigger_diag and session.events:
                g = self._graphs.get(session_id)
                full_diag = diagnose_session(session, g=g)
                session.diagnosis = full_diag.diagnosis
                session.full_diagnosis = full_diag

            session.transition_to(SessionStatus.COMPLETED)
            self.storage.update_session(session)
            self._metrics["completed"] += 1

            self._broadcast(session_id, {"type": "session_status", "status": session.status.value})
            if full_diag:
                self._broadcast(
                    session_id,
                    {"type": "diagnosis_complete", "diagnosis": full_diag.model_dump()},
                )

            return FinishSessionResponse(
                session_id=session_id,
                status=session.status,
                diagnosis=full_diag,
            )

    def diagnose_session(self, session_id: str) -> FullDiagnosisResponse:
        """
        Perform an on-demand diagnosis on a session (mid-session or completed).
        """
        lock = self._get_session_lock(session_id)
        with lock:
            session = self.storage.get_session(session_id)
            if not session:
                raise KeyError(f"Session '{session_id}' not found.")

            if not session.events:
                raise ValueError(f"Session '{session_id}' has no events to diagnose.")

            g = self._graphs.get(session_id)
            full_diag = diagnose_session(session, g=g)

            # Store updated diagnosis cache on session
            session.diagnosis = full_diag.diagnosis
            session.full_diagnosis = full_diag
            self.storage.update_session(session)

            self._broadcast(
                session_id,
                {"type": "diagnosis_complete", "diagnosis": full_diag.model_dump()},
            )

            return full_diag

    def get_session(self, session_id: str) -> Optional[TraceSession]:
        """Retrieve full TraceSession model by ID."""
        return self.storage.get_session(session_id)

    def get_graph(self, session_id: str) -> Optional[nx.DiGraph]:
        """Retrieve in-memory NetworkX DiGraph for a session."""
        return self._graphs.get(session_id)

    def list_sessions(
        self,
        status: Optional[SessionStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[SessionSummary], int]:
        """List session summaries with optional filtering and pagination."""
        return self.storage.list_sessions(status=status, limit=limit, offset=offset)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and clear its graph."""
        lock = self._get_session_lock(session_id)
        with lock:
            deleted = self.storage.delete_session(session_id)
            if session_id in self._graphs:
                del self._graphs[session_id]
            return deleted

    def get_analytics_summary(self) -> Dict[str, Any]:
        """
        Compute system-wide agent reliability analytics across all active/completed sessions.
        Includes failure taxonomy breakdown, event volume metrics, and root cause hotspots.
        """
        with self._global_lock:
            summaries, total = self.storage.list_sessions(limit=500, offset=0)

        status_counts: Dict[str, int] = {}
        failure_counts: Dict[str, int] = {}
        total_events = 0
        diagnosed_sessions = 0
        root_cause_hotspots: Dict[str, int] = {}

        for summary in summaries:
            status_counts[summary.status.value] = status_counts.get(summary.status.value, 0) + 1
            total_events += summary.event_count

            # Retrieve session details if diagnosis exists
            full_session = self.storage.get_session(summary.session_id)
            if full_session and full_session.diagnosis:
                diagnosed_sessions += 1
                cat = full_session.diagnosis.failure_category
                failure_counts[cat] = failure_counts.get(cat, 0) + 1

                rc_node = full_session.diagnosis.root_cause_node_id
                root_cause_hotspots[rc_node] = root_cause_hotspots.get(rc_node, 0) + 1

        avg_events = round(total_events / max(1, total), 2)

        return {
            "total_sessions": total,
            "total_events_ingested": total_events,
            "avg_events_per_session": avg_events,
            "diagnosed_sessions_count": diagnosed_sessions,
            "status_breakdown": status_counts,
            "failure_taxonomy_distribution": failure_counts,
            "root_cause_hotspots": root_cause_hotspots,
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Return operational metrics."""
        return {
            "sessions_created": self._metrics["created"],
            "sessions_completed": self._metrics["completed"],
            "sessions_failed": self._metrics["failed"],
            "sessions_expired": self._metrics["expired"],
            "events_ingested": self._metrics["events_ingested"],
            "active_sessions": len(self.storage.list_active_session_ids()),
            "total_sessions": self.storage.count_total(),
        }
