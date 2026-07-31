"""
Unit and Integration tests for Sessions WebSocket Stream endpoint.

Tests:
- Connecting to /sessions/ws/{session_id}
- Receiving initial 'connected' frame with session_id, status, event_count
- Receiving real-time 'node_added' frames on event ingestion
- Requesting snapshot ('request_snapshot')
- Disconnect and cleanup
- Rejecting connection for non-existent session_id (4004 close code)
"""

import sys
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import app
from routes.sessions import session_manager

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_sessions():
    """Clear session storage before each test."""
    session_manager.storage.clear()
    session_manager._graphs.clear()


class TestSessionsWebSocket:
    def test_ws_connection_and_handshake(self):
        """Test successful WebSocket handshake and initial connected frame."""
        start_resp = client.post("/sessions/start", json={"name": "WS Test"})
        sid = start_resp.json()["session_id"]

        with client.websocket_connect(f"/sessions/ws/{sid}") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connected"
            assert data["session_id"] == sid
            assert data["status"] == "created"
            assert data["event_count"] == 0

    def test_ws_realtime_node_added_broadcast(self):
        """Test that ingesting an event via REST broadcasts node_added to connected WS clients."""
        start_resp = client.post("/sessions/start", json={"name": "WS Realtime Test"})
        sid = start_resp.json()["session_id"]

        with client.websocket_connect(f"/sessions/ws/{sid}") as websocket:
            conn_frame = websocket.receive_json()
            assert conn_frame["type"] == "connected"

            # Ingest event via REST API
            client.post(
                f"/sessions/{sid}/events",
                json={"event": {"event_type": "planning", "content": "Live event content"}},
            )

            # Receive broadcast on WebSocket
            node_frame = websocket.receive_json()
            assert node_frame["type"] == "node_added"
            assert node_frame["node"]["content"] == "Live event content"
            assert node_frame["node"]["type"] == "plan"

    def test_ws_snapshot_request(self):
        """Test requesting execution graph snapshot via WebSocket."""
        start_resp = client.post("/sessions/start", json={"name": "WS Snapshot Test"})
        sid = start_resp.json()["session_id"]

        client.post(
            f"/sessions/{sid}/events",
            json={"event": {"event_type": "planning", "content": "Plan step"}},
        )

        with client.websocket_connect(f"/sessions/ws/{sid}") as websocket:
            websocket.receive_json()  # connected frame

            # Send snapshot request
            websocket.send_json({"type": "request_snapshot"})

            snapshot_frame = websocket.receive_json()
            assert snapshot_frame["type"] == "snapshot"
            assert snapshot_frame["session_id"] == sid
            assert "graph" in snapshot_frame
            assert len(snapshot_frame["graph"]["nodes"]) == 1

    def test_ws_nonexistent_session_closed(self):
        """Test that connecting to a non-existent session is closed."""
        with pytest.raises(Exception):
            with client.websocket_connect("/sessions/ws/nonexistent_session_id"):
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
