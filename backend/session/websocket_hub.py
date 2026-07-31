"""
WebSocket Connection Manager Hub for TraceMind Live Sessions.

Manages active WebSocket connections per session, broadcasts real-time graph updates,
node/edge creation events, anomaly flags, and diagnosis completion notifications.
Handles heartbeats (ping/pong) and clean disconnection.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
import logging
from typing import Any, Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("tracemind.websocket")


class WebSocketHub:
    """
    Thread-safe connection manager for real-time session WebSocket streams.
    """

    def __init__(self) -> None:
        self._connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, session_id: str, ws: WebSocket) -> None:
        """Accept and register a WebSocket client connection for a session."""
        await ws.accept()
        async with self._lock:
            self._connections[session_id].add(ws)
        logger.info(f"WebSocket client connected to session '{session_id}'")

    async def disconnect(self, session_id: str, ws: WebSocket) -> None:
        """Unregister a WebSocket client connection."""
        async with self._lock:
            if session_id in self._connections:
                self._connections[session_id].discard(ws)
                if not self._connections[session_id]:
                    del self._connections[session_id]
        logger.info(f"WebSocket client disconnected from session '{session_id}'")

    async def broadcast(self, session_id: str, message: Dict[str, Any]) -> None:
        """
        Broadcast a JSON message to all clients connected to a specific session.
        Stale/broken connections are automatically disconnected.
        """
        async with self._lock:
            clients = list(self._connections.get(session_id, set()))

        if not clients:
            return

        stale: List[WebSocket] = []
        for ws in clients:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Error broadcasting to WebSocket in session '{session_id}': {e}")
                stale.append(ws)

        if stale:
            for ws in stale:
                await self.disconnect(session_id, ws)

    async def close_all(self, reason: str = "Server shutting down") -> None:
        """Close all active WebSocket connections across all sessions."""
        async with self._lock:
            all_sessions = list(self._connections.keys())

        for sid in all_sessions:
            async with self._lock:
                clients = list(self._connections.get(sid, set()))
            for ws in clients:
                try:
                    await ws.close(code=1001, reason=reason)
                except Exception:
                    pass
            async with self._lock:
                self._connections.pop(sid, None)

    def connection_count(self, session_id: Optional[str] = None) -> int:
        """Return total active WebSocket connections or connections for a session."""
        if session_id:
            return len(self._connections.get(session_id, set()))
        return sum(len(clients) for clients in self._connections.values())

    async def heartbeat_loop(self, interval_seconds: int = 30) -> None:
        """
        Periodic background task that sends ping messages to all connected clients.
        """
        while True:
            await asyncio.sleep(interval_seconds)
            async with self._lock:
                all_sessions = list(self._connections.keys())

            for sid in all_sessions:
                await self.broadcast(sid, {"type": "ping"})
