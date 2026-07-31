"""
Storage backends for TraceMind session persistence.

Provides an abstract StorageBackend interface and an InMemoryStorage
implementation for development. The interface is designed so that
SQLite/PostgreSQL backends can be swapped in without changing business logic.
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

try:
    from models.session import (
        SessionStatus,
        SessionSummary,
        TraceSession,
    )
except ImportError:
    from backend.models.session import (
        SessionStatus,
        SessionSummary,
        TraceSession,
    )


class StorageBackend(ABC):
    """Abstract storage interface for session persistence."""

    @abstractmethod
    def create_session(self, session: TraceSession) -> None:
        """Store a new session. Raises ValueError if session_id already exists."""
        ...

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[TraceSession]:
        """Retrieve a session by ID, or None if not found."""
        ...

    @abstractmethod
    def update_session(self, session: TraceSession) -> None:
        """Update an existing session. Raises ValueError if not found."""
        ...

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID. Returns True if deleted, False if not found."""
        ...

    @abstractmethod
    def list_sessions(
        self,
        status: Optional[SessionStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[SessionSummary], int]:
        """
        List session summaries with optional status filter and pagination.
        Returns (items, total_count).
        """
        ...

    @abstractmethod
    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        ...

    @abstractmethod
    def count_by_status(self, status: SessionStatus) -> int:
        """Count sessions with the given status."""
        ...

    @abstractmethod
    def count_total(self) -> int:
        """Count total sessions."""
        ...

    @abstractmethod
    def list_active_session_ids(self) -> List[str]:
        """List session IDs that are in non-terminal states."""
        ...


class InMemoryStorage(StorageBackend):
    """
    Thread-safe in-memory storage for development and testing.

    All sessions are stored in a dictionary keyed by session_id.
    Thread safety is provided by a reentrant lock.
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, TraceSession] = {}
        self._lock = threading.RLock()

    def create_session(self, session: TraceSession) -> None:
        with self._lock:
            if session.session_id in self._sessions:
                raise ValueError(
                    f"Session '{session.session_id}' already exists"
                )
            self._sessions[session.session_id] = session

    def get_session(self, session_id: str) -> Optional[TraceSession]:
        with self._lock:
            return self._sessions.get(session_id)

    def update_session(self, session: TraceSession) -> None:
        with self._lock:
            if session.session_id not in self._sessions:
                raise ValueError(
                    f"Session '{session.session_id}' not found for update"
                )
            self._sessions[session.session_id] = session

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False

    def list_sessions(
        self,
        status: Optional[SessionStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[SessionSummary], int]:
        with self._lock:
            all_sessions = list(self._sessions.values())

        # Apply status filter
        if status is not None:
            all_sessions = [s for s in all_sessions if s.status == status]

        # Sort by created_at descending (newest first)
        all_sessions.sort(key=lambda s: s.created_at, reverse=True)

        total = len(all_sessions)

        # Apply pagination
        page = all_sessions[offset : offset + limit]
        summaries = [SessionSummary.from_session(s) for s in page]

        return summaries, total

    def session_exists(self, session_id: str) -> bool:
        with self._lock:
            return session_id in self._sessions

    def count_by_status(self, status: SessionStatus) -> int:
        with self._lock:
            return sum(
                1 for s in self._sessions.values() if s.status == status
            )

    def count_total(self) -> int:
        with self._lock:
            return len(self._sessions)

    def list_active_session_ids(self) -> List[str]:
        with self._lock:
            non_terminal = {
                SessionStatus.CREATED,
                SessionStatus.RUNNING,
                SessionStatus.COMPLETING,
            }
            return [
                sid
                for sid, s in self._sessions.items()
                if s.status in non_terminal
            ]

    def clear(self) -> None:
        """Clear all sessions. Useful for testing."""
        with self._lock:
            self._sessions.clear()
