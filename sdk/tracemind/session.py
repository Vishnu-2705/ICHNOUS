"""
Synchronous Session Client for TraceMind SDK.

Enables AI agents to instrument execution runs with zero hassle:
- Automatic session allocation on init
- Automatic timestamp and sequence numbering
- Automatic reads_from dependency linking
- Context manager support (`with tm.Session(...) as session:`)
- Automatic error capture and diagnosis triggering on finish
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import requests

from tracemind.exceptions import ConnectionError, SessionError, ValidationError
from tracemind.models import EventType

logger = logging.getLogger("tracemind.sdk")


class Session:
    """
    Synchronous live trace session client.
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        backend_url: str = "http://localhost:8000",
        tags: Optional[Dict[str, str]] = None,
        ttl_seconds: int = 3600,
        auto_link: bool = True,
        auto_timestamp: bool = True,
        api_key: Optional[str] = None,
    ) -> None:
        if not name or not name.strip():
            raise ValidationError("Session name must not be empty.")

        self.name = name.strip()
        self.description = description
        self.backend_url = backend_url.rstrip("/")
        self.tags = tags or {}
        self.ttl_seconds = ttl_seconds
        self.auto_link = auto_link
        self.auto_timestamp = auto_timestamp
        self.api_key = api_key

        self._event_counter = 0
        self._last_event_id: Optional[str] = None
        self._session_id: Optional[str] = None
        self._ws_url: Optional[str] = None
        self._is_finished = False

        self._headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            self._headers["X-API-Key"] = self.api_key

        # Create session on backend
        self._start_session()

    def _start_session(self) -> None:
        url = f"{self.backend_url}/sessions/start"
        payload = {
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "ttl_seconds": self.ttl_seconds,
        }
        try:
            resp = requests.post(url, json=payload, headers=self._headers, timeout=10)
        except requests.RequestException as e:
            raise ConnectionError(
                f"Could not connect to TraceMind backend at '{url}': {e}"
            ) from e

        if resp.status_code != 201:
            raise SessionError(
                f"Failed to create session on backend (HTTP {resp.status_code}): {resp.text}"
            )

        data = resp.json()
        self._session_id = data["session_id"]
        self._ws_url = data["ws_url"]

    @property
    def session_id(self) -> str:
        if not self._session_id:
            raise SessionError("Session has not been initialized.")
        return self._session_id

    @property
    def ws_url(self) -> str:
        return self._ws_url or ""

    def emit(
        self,
        event_type: str | EventType,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        reads_from: Optional[List[str]] = None,
        parent_event_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        event_id: Optional[str] = None,
    ) -> str:
        """
        Emit a single agent execution event.

        Returns the assigned event_id string.
        """
        if self._is_finished:
            raise SessionError(f"Cannot emit event on finished session '{self._session_id}'.")

        if not content or not content.strip():
            raise ValidationError("Event content must not be empty.")

        etype = event_type.value if isinstance(event_type, EventType) else str(event_type)

        self._event_counter += 1
        eid = event_id or f"evt_{self._event_counter}"
        timestamp = datetime.now(timezone.utc).isoformat() if self.auto_timestamp else ""

        # Handle auto-linking dependency resolution
        resolved_reads_from = reads_from
        if resolved_reads_from is None and self.auto_link:
            resolved_reads_from = [self._last_event_id] if self._last_event_id else []

        event_payload = {
            "event_id": eid,
            "event_type": etype,
            "timestamp": timestamp,
            "content": content,
            "metadata": metadata or {},
            "reads_from": resolved_reads_from,
            "parent_event_id": parent_event_id,
            "agent_id": agent_id,
            "sequence_number": self._event_counter,
        }

        url = f"{self.backend_url}/sessions/{self._session_id}/events"
        try:
            resp = requests.post(url, json={"event": event_payload}, headers=self._headers, timeout=10)
        except requests.RequestException as e:
            raise ConnectionError(
                f"Failed to send event to TraceMind backend at '{url}': {e}"
            ) from e

        if resp.status_code not in (200, 201):
            raise SessionError(
                f"Event ingestion failed (HTTP {resp.status_code}): {resp.text}"
            )

        self._last_event_id = eid
        return eid

    def emit_error(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Convenience helper to emit an error event."""
        return self.emit(EventType.ERROR, content, metadata=metadata)

    def finish(self, trigger_diagnosis: bool = True) -> Dict[str, Any]:
        """
        Finalize the session and optionally trigger diagnosis.
        """
        if self._is_finished:
            url = f"{self.backend_url}/sessions/{self._session_id}"
            resp = requests.get(url, headers=self._headers, timeout=10)
            return resp.json() if resp.status_code == 200 else {}

        url = f"{self.backend_url}/sessions/{self._session_id}/finish"
        payload = {"trigger_diagnosis": trigger_diagnosis}
        try:
            resp = requests.post(url, json=payload, headers=self._headers, timeout=30)
        except requests.RequestException as e:
            raise ConnectionError(
                f"Failed to finish session on TraceMind backend at '{url}': {e}"
            ) from e

        if resp.status_code != 200:
            raise SessionError(
                f"Session finish failed (HTTP {resp.status_code}): {resp.text}"
            )

        self._is_finished = True
        return resp.json()

    def __enter__(self) -> "Session":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is not None:
            try:
                self.emit_error(
                    content=f"Agent exception: {exc_val}",
                    metadata={"exception_type": str(exc_type.__name__)},
                )
            except Exception as e:
                logger.warning(f"Could not emit exception event: {e}")

        try:
            self.finish(trigger_diagnosis=True)
        except Exception as e:
            logger.warning(f"Could not finish session cleanly on exit: {e}")

        return False  # Re-raise exceptions if present
