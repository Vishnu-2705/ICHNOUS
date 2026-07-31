"""Unit tests for FastAPI API Endpoints layer."""

import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import app
from models.trace import FullDiagnosisResponse, RegressionTest, Trace, TraceSummary

client = TestClient(app)


def test_get_traces():
    """Test GET /traces endpoint."""
    response = client.get("/traces")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3

    # Validate schema for each item against TraceSummary
    summaries = [TraceSummary.model_validate(item) for item in data]
    ids = {s.id for s in summaries}
    assert "trace_retrieval" in ids
    assert "trace_tool" in ids
    assert "trace_coordination" in ids


def test_get_trace_by_id_success():
    """Test GET /traces/{id} endpoint with valid ID."""
    response = client.get("/traces/trace_retrieval")
    assert response.status_code == 200
    data = response.json()
    trace = Trace.model_validate(data)
    assert trace.id == "trace_retrieval"
    assert trace.name == "Retrieval Failure — Stale Refund Policy"
    assert len(trace.nodes) > 0


def test_get_trace_by_id_not_found():
    """Test GET /traces/{id} endpoint with invalid ID."""
    response = client.get("/traces/non_existent_trace_123")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_post_diagnose_success():
    """Test POST /traces/{id}/diagnose endpoint with valid ID."""
    response = client.post("/traces/trace_retrieval/diagnose")
    assert response.status_code == 200
    data = response.json()
    diag_resp = FullDiagnosisResponse.model_validate(data)

    assert diag_resp.diagnosis.root_cause_node_id == "node_2"
    assert diag_resp.diagnosis.failure_category == "Retrieval"
    assert isinstance(diag_resp.anomalies, list)
    assert isinstance(diag_resp.critical_path, list)
    assert "nodes" in diag_resp.graph
    assert "edges" in diag_resp.graph


def test_graph_serialization_schema():
    """Verify graph serialization outputs AGENTS.md §10 fields (source/target, is_root_cause...)."""
    response = client.post("/traces/trace_retrieval/diagnose")
    data = response.json()
    nodes = data["graph"]["nodes"]
    edges = data["graph"]["edges"]

    assert len(nodes) > 0
    assert "id" in nodes[0]
    assert "is_root_cause" in nodes[0]
    assert "is_evidence" in nodes[0]
    assert "is_critical_path" in nodes[0]

    assert len(edges) > 0
    assert "source" in edges[0]
    assert "target" in edges[0]
    assert "from" in edges[0]
    assert "to" in edges[0]


def test_all_three_fixtures_fallback_categories():
    """Verify all 3 trace fixtures diagnose to exact expected taxonomy categories with no API key."""
    for trace_id, expected_cat in [
        ("retrieval_failure", "Retrieval"),
        ("tool_failure", "Tool"),
        ("coordination_failure", "Coordination"),
    ]:
        resp = client.post(f"/traces/{trace_id}/diagnose")
        assert resp.status_code == 200
        cat = resp.json()["diagnosis"]["failure_category"]
        assert cat == expected_cat, f"Trace '{trace_id}' expected category '{expected_cat}', got '{cat}'"


def test_post_diagnose_not_found():
    """Test POST /traces/{id}/diagnose endpoint with invalid ID."""
    response = client.post("/traces/non_existent_trace_123/diagnose")
    assert response.status_code == 404


def test_post_regression_test_success():
    """Test POST /traces/{id}/regression-test endpoint with valid ID."""
    response = client.post("/traces/trace_retrieval/regression-test")
    assert response.status_code == 200
    data = response.json()
    reg_test = RegressionTest.model_validate(data)

    assert reg_test.trace_id == "trace_retrieval"
    assert reg_test.root_cause_node_id == "node_2"
    assert "initial_task" in reg_test.minimal_inputs
    assert reg_test.assertion.failure_category is not None


def test_post_regression_test_not_found():
    """Test POST /traces/{id}/regression-test endpoint with invalid ID."""
    response = client.post("/traces/non_existent_trace_123/regression-test")
    assert response.status_code == 404


def test_post_run_regression_success():
    """Test POST /traces/{id}/run-regression endpoint with valid ID."""
    response = client.post("/traces/trace_retrieval/run-regression")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PASSED"
    assert data["baseline_status"] == "FAILED_AS_EXPECTED"
    assert data["patched_status"] == "PASSED"
    assert len(data["logs"]) > 0


if __name__ == "__main__":
    test_get_traces()
    test_get_trace_by_id_success()
    test_get_trace_by_id_not_found()
    test_post_diagnose_success()
    test_graph_serialization_schema()
    test_all_three_fixtures_fallback_categories()
    test_post_diagnose_not_found()
    test_post_regression_test_success()
    test_post_regression_test_not_found()
    test_post_run_regression_success()
    print("All API Endpoints unit tests passed successfully!")

