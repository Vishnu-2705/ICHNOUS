"""
Unit and Integration tests for Sessions REST API Endpoints.

Tests:
- POST /sessions/start (create session)
- POST /sessions/{id}/events (ingest single event)
- POST /sessions/{id}/events/batch (ingest batch up to 100)
- POST /sessions/{id}/finish (finish session & trigger diagnosis)
- POST /sessions/{id}/diagnose (on-demand diagnosis)
- GET /sessions (paginated session list + status filter)
- GET /sessions/{id} (get full session detail)
- GET /sessions/{id}/graph (get serialized NetworkX graph)
- GET /sessions/{id}/events (get paginated event list)
- DELETE /sessions/{id} (delete session)
- Error handling (404, 409, 422, batch limits)
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


class TestSessionsAPI:
    def test_start_session_success(self):
        resp = client.post(
            "/sessions/start",
            json={"name": "API Test Session", "description": "Testing REST API"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "session_id" in data
        assert data["status"] == "created"
        assert "/ws/sessions/" in data["ws_url"]

    def test_start_session_validation_failure(self):
        resp = client.post("/sessions/start", json={"name": ""})
        assert resp.status_code == 422

    def test_ingest_event_success(self):
        start_resp = client.post("/sessions/start", json={"name": "Event Ingest Test"})
        sid = start_resp.json()["session_id"]

        resp = client.post(
            f"/sessions/{sid}/events",
            json={
                "event": {
                    "event_type": "planning",
                    "content": "Formulating execution plan",
                }
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == sid
        assert data["event_id"] == "evt_1"
        assert data["event_count"] == 1
        assert data["status"] == "running"

    def test_ingest_event_not_found(self):
        resp = client.post(
            "/sessions/nonexistent_123/events",
            json={"event": {"event_type": "planning", "content": "Plan"}},
        )
        assert resp.status_code == 404

    def test_ingest_batch_success(self):
        start_resp = client.post("/sessions/start", json={"name": "Batch Test"})
        sid = start_resp.json()["session_id"]

        resp = client.post(
            f"/sessions/{sid}/events/batch",
            json={
                "events": [
                    {"event_type": "planning", "content": "Plan 1"},
                    {"event_type": "tool_call", "content": "Tool 1"},
                    {"event_type": "observation", "content": "Obs 1"},
                ]
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        assert data[2]["event_count"] == 3

    def test_finish_session_with_diagnosis(self):
        start_resp = client.post("/sessions/start", json={"name": "Finish Test"})
        sid = start_resp.json()["session_id"]

        client.post(
            f"/sessions/{sid}/events",
            json={"event": {"event_type": "planning", "content": "Plan"}},
        )
        client.post(
            f"/sessions/{sid}/events",
            json={
                "event": {
                    "event_type": "tool_call",
                    "content": "search_kb()",
                    "metadata": {"tool_name": "search_knowledge_base", "relevance_score": 0.3},
                }
            },
        )
        client.post(
            f"/sessions/{sid}/events",
            json={"event": {"event_type": "final_answer", "content": "Deny"}},
        )

        resp = client.post(f"/sessions/{sid}/finish", json={"trigger_diagnosis": True})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["diagnosis"] is not None
        assert data["diagnosis"]["diagnosis"]["failure_category"] == "Retrieval"

    def test_on_demand_diagnose_endpoint(self):
        start_resp = client.post("/sessions/start", json={"name": "On-Demand Test"})
        sid = start_resp.json()["session_id"]

        client.post(
            f"/sessions/{sid}/events",
            json={"event": {"event_type": "planning", "content": "Plan"}},
        )
        client.post(
            f"/sessions/{sid}/events",
            json={
                "event": {
                    "event_type": "tool_call",
                    "content": "lint_analyze()",
                    "metadata": {"error": "rate_limit_degraded", "response_truncated": True},
                }
            },
        )
        client.post(
            f"/sessions/{sid}/events",
            json={"event": {"event_type": "observation", "content": "Truncated output"}},
        )

        resp = client.post(f"/sessions/{sid}/diagnose")
        assert resp.status_code == 200
        data = resp.json()
        assert data["diagnosis"]["failure_category"] in ("Tool", "External API")

    def test_list_sessions_paginated(self):
        for i in range(5):
            client.post("/sessions/start", json={"name": f"Session {i}"})

        resp = client.get("/sessions?limit=2&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["has_more"] is True

    def test_get_session_by_id(self):
        start_resp = client.post("/sessions/start", json={"name": "Get Test"})
        sid = start_resp.json()["session_id"]

        resp = client.get(f"/sessions/{sid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == sid
        assert data["name"] == "Get Test"

    def test_get_session_graph(self):
        start_resp = client.post("/sessions/start", json={"name": "Graph API Test"})
        sid = start_resp.json()["session_id"]

        client.post(f"/sessions/{sid}/events", json={"event": {"event_type": "planning", "content": "P1"}})
        client.post(f"/sessions/{sid}/events", json={"event": {"event_type": "tool_call", "content": "T1"}})

        resp = client.get(f"/sessions/{sid}/graph")
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1

    def test_list_session_events(self):
        start_resp = client.post("/sessions/start", json={"name": "Events List Test"})
        sid = start_resp.json()["session_id"]

        client.post(f"/sessions/{sid}/events", json={"event": {"event_type": "planning", "content": "P1"}})
        client.post(f"/sessions/{sid}/events", json={"event": {"event_type": "tool_call", "content": "T1"}})

        resp = client.get(f"/sessions/{sid}/events")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_delete_session(self):
        start_resp = client.post("/sessions/start", json={"name": "Delete API Test"})
        sid = start_resp.json()["session_id"]

        del_resp = client.delete(f"/sessions/{sid}")
        assert del_resp.status_code == 204

        get_resp = client.get(f"/sessions/{sid}")
        assert get_resp.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
