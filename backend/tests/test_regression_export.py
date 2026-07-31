"""
Unit tests for Regression Test export endpoint.
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent
project_dir = backend_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

from app import app

client = TestClient(app)


class TestRegressionExport:
    def test_export_regression_test(self):
        # 1. Start session
        start_resp = client.post("/sessions/start", json={"name": "Regression Export Test"})
        assert start_resp.status_code == 201
        session_id = start_resp.json()["session_id"]

        # 2. Transition session to running by ingesting an event
        evt_resp = client.post(f"/sessions/{session_id}/events", json={
            "event": {
                "event_id": "evt_reg_001",
                "event_type": "planning",
                "content": "Plan step",
            }
        })
        assert evt_resp.status_code == 200

        # 3. Finish session
        finish_resp = client.post(f"/sessions/{session_id}/finish")
        assert finish_resp.status_code == 200

        # 4. Export regression test script
        resp = client.get(f"/sessions/{session_id}/export-regression-test")
        assert resp.status_code == 200
        data = resp.json()
        assert "pytest_code" in data
        assert "def test_agent_regression" in data["pytest_code"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
