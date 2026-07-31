"""
Unit tests for Source Code Upload & Analysis API router.
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure sys.path includes backend and project root
backend_dir = Path(__file__).resolve().parent.parent
project_dir = backend_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

from app import app

client = TestClient(app)


class TestUploadAPI:
    def test_analyze_code_text_langgraph(self):
        sample_code = """
import tracemind.auto
from langgraph.graph import StateGraph

def search_kb(state):
    return {"docs": "stale 2023 refund policy"}

graph = StateGraph()
        """
        response = client.post(
            "/upload/analyze-code",
            json={
                "code_text": sample_code,
                "framework": "langgraph",
                "session_name": "Test Uploaded LangGraph Agent",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["framework"] == "langgraph"
        assert data["diagnosis"] is not None
        assert "verification" in data
        assert "verified" in data["verification"]

    def test_analyze_code_text_crewai(self):
        sample_code = "from crewai import Agent, Crew\ndef execute_tool(): pass"

        response = client.post(
            "/upload/analyze-code",
            json={
                "code_text": sample_code,
                "framework": "crewai",
                "session_name": "Uploaded CrewAI Agent Code",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["framework"] == "crewai"
        assert data["diagnosis"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
