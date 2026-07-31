"""
Asynchronous Session Client for TraceMind SDK.

Enables async AI agents (LangChain Async, AutoGen, CrewAI Async) to instrument
runs asynchronously with httpx:
- Async context manager (`async with tm.AsyncSession(...) as session:`)
- Non-blocking HTTP event emission
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import httpx

from tracemind.exceptions import ConnectionError, SessionError, ValidationError
from tracemind.models import EventType

logger = logging.getLogger("tracemind.sdk.async")


class AsyncSession:
    """
    Asynchronous live trace session client.
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
        self._client: Optional[httpx.AsyncClient] = None

        self._headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            self._headers["X-API-Key"] = self.api_key

    async def initialize(self) -> "AsyncSession":
        """Initialize async HTTP client and create session on backend."""
        if not self._client:
            self._client = httpx.AsyncClient(headers=self._headers, timeout=10.0)

        url = f"{self.backend_url}/sessions/start"
        payload = {
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "ttl_seconds": self.ttl_seconds,
        }
        try:
            resp = await self._client.post(url, json=payload)
        except httpx.HTTPError as e:
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
        return self

    @property
    def session_id(self) -> str:
        if not self._session_id:
            raise SessionError("AsyncSession has not been initialized.")
        return self._session_id

    @property
    def ws_url(self) -> str:
        return self._ws_url or ""

    async def emit(
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
        Asynchronously emit a single agent execution event.
        """
        if not self._client or not self._session_id:
            await self.initialize()

        if self._is_finished:
            raise SessionError(f"Cannot emit event on finished session '{self._session_id}'.")

        if not content or not content.strip():
            raise ValidationError("Event content must not be empty.")

        etype = event_type.value if isinstance(event_type, EventType) else str(event_type)

        self._event_counter += 1
        eid = event_id or f"evt_{self._event_counter}"
        timestamp = datetime.now(timezone.utc).isoformat() if self.auto_timestamp else ""

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
            resp = await self._client.post(url, json={"event": event_payload})
        except httpx.HTTPError as e:
            raise ConnectionError(
                f"Failed to send event to TraceMind backend at '{url}': {e}"
            ) from e

        if resp.status_code not in (200, 201):
            raise SessionError(
                f"Event ingestion failed (HTTP {resp.status_code}): {resp.text}"
            )

        self._last_event_id = eid
        return eid

    async def emit_error(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Convenience helper to emit an error event."""
        return await self.emit(EventType.ERROR, content, metadata=metadata)

    async def finish(self, trigger_diagnosis: bool = True) -> Dict[str, Any]:
        """
        Asynchronously finalize session and optionally trigger diagnosis.
        """
        if not self._client or not self._session_id:
            return {}

        if self._is_finished:
            url = f"{self.backend_url}/sessions/{self._session_id}"
            resp = await self._client.get(url)
            return resp.json() if resp.status_code == 200 else {}

        url = f"{self.backend_url}/sessions/{self._session_id}/finish"
        payload = {"trigger_diagnosis": trigger_diagnosis}
        try:
            resp = await self._client.post(url, json=payload, timeout=30.0)
        except httpx.HTTPError as e:
            raise ConnectionError(
                f"Failed to finish session on TraceMind backend at '{url}': {e}"
            ) from e

        if resp.status_code != 200:
            raise SessionError(
                f"Session finish failed (HTTP {resp.status_code}): {resp.text}"
            )

        self._is_finished = True
        return resp.json()

    async def close(self) -> None:
        """Close the underlying httpx AsyncClient."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "AsyncSession":
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is not None:
            try:
                await self.emit_error(
                    content=f"Agent exception: {exc_val}",
                    metadata={"exception_type": str(exc_type.__name__)},
                )
            except Exception as e:
                logger.warning(f"Could not emit exception event: {e}")

        try:
            await self.finish(trigger_diagnosis=True)
        except Exception as e:
            logger.warning(f"Could not finish session cleanly on exit: {e}")
        finally:
            await self.close()

        return False
