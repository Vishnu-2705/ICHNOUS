"""
Integration tests for Agent 365 REST API Endpoints.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

# Ensure sys.path includes backend and project root
backend_dir = Path(__file__).resolve().parent.parent
project_dir = backend_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

from backend.app import app

client = TestClient(app)


class TestAgent365API:
    def test_post_agent365_diagnose(self):
        payload = {
            "spans": [
                {
                    "span_id": "sp_1",
                    "trace_id": "tr_api_1",
                    "name": "plan",
                    "attributes": {"openinference.span.kind": "AGENT", "input.value": "Query"},
                },
                {
                    "span_id": "sp_2",
                    "parent_span_id": "sp_1",
                    "trace_id": "tr_api_1",
                    "name": "search_knowledge_base",
                    "attributes": {
                        "openinference.span.kind": "TOOL",
                        "tool.name": "search_knowledge_base",
                        "retrieval.relevance_score": 0.35,
                        "note": "stale document",
                    },
                },
                {
                    "span_id": "sp_3",
                    "parent_span_id": "sp_2",
                    "trace_id": "tr_api_1",
                    "name": "final_answer",
                    "attributes": {"openinference.span.kind": "CHAIN", "output.value": "Denied"},
                },
            ]
        }

        resp = client.post("/agent365/diagnose", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["diagnosis"]["failure_category"] == "Retrieval"
        assert data["diagnosis"]["root_cause_node_id"] == "sp_2"

    def test_post_agent365_phoenix_diagnose_mocked(self):
        mock_get_res = MagicMock()
        mock_get_res.status_code = 200
        mock_get_res.json.return_value = {
            "spans": [
                {
                    "span_id": "ph_1",
                    "trace_id": "ph_tr_1",
                    "name": "plan",
                    "attributes": {"openinference.span.kind": "AGENT", "input.value": "Test"},
                },
                {
                    "span_id": "ph_2",
                    "parent_span_id": "ph_1",
                    "trace_id": "ph_tr_1",
                    "name": "search_knowledge_base",
                    "attributes": {
                        "openinference.span.kind": "TOOL",
                        "tool.name": "search_knowledge_base",
                        "retrieval.relevance_score": 0.2,
                        "note": "stale policy",
                    },
                },
                {
                    "span_id": "ph_3",
                    "parent_span_id": "ph_2",
                    "trace_id": "ph_tr_1",
                    "name": "final_answer",
                    "attributes": {"openinference.span.kind": "CHAIN", "output.value": "Done"},
                },
            ]
        }

        mock_post_res = MagicMock()
        mock_post_res.status_code = 201

        payload = {
            "phoenix_url": "http://localhost:6006",
            "trace_id": "ph_tr_1",
            "annotate": True,
        }

        with patch("requests.get", return_value=mock_get_res), patch("requests.post", return_value=mock_post_res):
            resp = client.post("/agent365/phoenix/diagnose", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert data["diagnosis"]["root_cause_node_id"] == "ph_2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
