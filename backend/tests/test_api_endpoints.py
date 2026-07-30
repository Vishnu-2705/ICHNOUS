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
    assert diag_resp.diagnosis.failure_category in ["Retrieval", "Unknown"]
    assert isinstance(diag_resp.anomalies, list)
    assert isinstance(diag_resp.critical_path, list)
    assert "nodes" in diag_resp.graph
    assert "edges" in diag_resp.graph


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


if __name__ == "__main__":
    test_get_traces()
    test_get_trace_by_id_success()
    test_get_trace_by_id_not_found()
    test_post_diagnose_success()
    test_post_diagnose_not_found()
    test_post_regression_test_success()
    test_post_regression_test_not_found()
    print("All API Endpoints unit tests passed successfully!")
