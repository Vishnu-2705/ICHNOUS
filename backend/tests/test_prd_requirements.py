"""
Unit tests verifying TraceMind PRD Requirements (FR-1 through FR-19).
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
from backend.graph.analyzer import get_top_k_root_cause_candidates
from backend.graph.builder import build_graph
from backend.models.trace import Trace, TraceNode, NodeType

client = TestClient(app)


class TestPRDRequirements:
    def test_fr3_disallowed_patterns_rejected(self):
        malicious_code = "import os\nos.system('rm -rf /')"
        response = client.post(
            "/upload/analyze-code",
            json={
                "code_text": malicious_code,
                "framework": "custom",
                "session_name": "Security Test",
            },
        )
        assert response.status_code == 400
        assert "Disallowed system command pattern" in response.json()["detail"]

    def test_fr10_top_k_root_cause_candidates(self):
        trace = Trace(
            id="t1",
            name="test_trace",
            description="test trace description",
            nodes=[
                TraceNode(id="e1", type=NodeType.PLAN, content="Plan", metadata={}, timestamp="2026-07-30T00:00:00Z"),
                TraceNode(id="e2", type=NodeType.TOOL_CALL, content="tool1", metadata={"relevance_score": 0.2}, reads_from=["e1"], timestamp="2026-07-30T00:00:01Z"),
                TraceNode(id="e3", type=NodeType.TOOL_CALL, content="tool2", metadata={"latency_ms": 6000}, reads_from=["e2"], timestamp="2026-07-30T00:00:02Z"),
                TraceNode(id="e4", type=NodeType.FINAL_ANSWER, content="Result", metadata={}, reads_from=["e3"], timestamp="2026-07-30T00:00:03Z"),
            ],
        )
        g = build_graph(trace)
        top_cands = get_top_k_root_cause_candidates(g, k=3)
        assert len(top_cands) >= 1
        assert top_cands[0].divergence_score > 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
