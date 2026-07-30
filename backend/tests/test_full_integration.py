"""End-to-End Integration Verification Test Suite for TraceMind Backend."""

import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import app
from diagnosis.llm import diagnose_with_llm
from diagnosis.validator import validate_groundedness
from fixtures import get_all_fixtures, load_fixture_trace
from graph.analyzer import (
    backward_walk,
    compute_divergence,
    detect_anomalies,
    extract_critical_path,
    find_failure_node,
    rank_root_cause_candidates,
)
from graph.builder import build_graph, get_graph_statistics
from models.trace import (
    FullDiagnosisResponse,
    RegressionTest,
    Trace,
    TraceSummary,
)
from regression.generator import generate_regression_test

client = TestClient(app)


def verify_all_fixtures():
    """Verify loading and validating all trace fixtures."""
    fixtures = get_all_fixtures()
    assert len(fixtures) == 3
    for name, trace in fixtures.items():
        assert isinstance(trace, Trace)
        assert trace.id is not None
        assert len(trace.nodes) > 0
    print("[PASSED] Fixtures Verification")


def verify_graph_generation():
    """Verify networkx DiGraph construction and statistics for all fixtures."""
    fixtures = get_all_fixtures()
    for name, trace in fixtures.items():
        g = build_graph(trace)
        stats = get_graph_statistics(g)
        assert stats["num_nodes"] == len(trace.nodes)
        assert stats["num_edges"] >= 0
    print("[PASSED] Graph Generation Verification")


def verify_anomaly_detection():
    """Verify deterministic anomaly detection across all fixtures."""
    fixtures = get_all_fixtures()
    for name, trace in fixtures.items():
        g = build_graph(trace)
        anomalies = detect_anomalies(g)
        assert isinstance(anomalies, list)
    print("[PASSED] Anomaly Detection Verification")


def verify_critical_path_and_backward_walk():
    """Verify critical path extraction and backward causal walk for all fixtures."""
    fixtures = get_all_fixtures()
    for name, trace in fixtures.items():
        g = build_graph(trace)
        anomalies = detect_anomalies(g)
        cp = extract_critical_path(g)
        assert len(cp) > 0

        rc_candidate = backward_walk(g, cp, anomalies)
        assert rc_candidate.node_id is not None
        assert len(rc_candidate.evidence_node_ids) > 0

        # Verify candidate ranking
        ranked = rank_root_cause_candidates([rc_candidate])
        assert ranked is not None
        assert ranked.node_id == rc_candidate.node_id

    print("[PASSED] Backward Causal Walk & Ranking Verification")


def verify_diagnosis_and_groundedness():
    """Verify LLM diagnosis generation and groundedness validation."""
    fixtures = get_all_fixtures()
    for name, trace in fixtures.items():
        g = build_graph(trace)
        anomalies = detect_anomalies(g)
        cp = extract_critical_path(g)
        rc = backward_walk(g, cp, anomalies)

        evidence_nodes = [
            {"id": nid, "type": g.nodes[nid].get("type"), "content": g.nodes[nid].get("content"), "metadata": g.nodes[nid].get("metadata")}
            for nid in rc.evidence_node_ids
            if g.has_node(nid)
        ]

        diag_result = diagnose_with_llm(rc, evidence_nodes, g=g)
        validated = validate_groundedness(diag_result, g, candidate=rc)
        assert validated.failure_category is not None
        assert validated.confidence >= 0.1
    print("[PASSED] Diagnosis & Groundedness Verification")


def verify_regression_generator():
    """Verify regression test artifact generation."""
    fixtures = get_all_fixtures()
    for name, trace in fixtures.items():
        g = build_graph(trace)
        anomalies = detect_anomalies(g)
        cp = extract_critical_path(g)
        rc = backward_walk(g, cp, anomalies)

        evidence_nodes = [
            {"id": nid, "type": g.nodes[nid].get("type"), "content": g.nodes[nid].get("content"), "metadata": g.nodes[nid].get("metadata")}
            for nid in rc.evidence_node_ids
            if g.has_node(nid)
        ]

        diag = diagnose_with_llm(rc, evidence_nodes, g=g)
        reg_test = generate_regression_test(trace, diag, g)
        assert isinstance(reg_test, RegressionTest)
        assert reg_test.trace_id == trace.id
    print("[PASSED] Regression Generator Verification")


def verify_api_endpoints():
    """Verify all FastAPI REST endpoints using TestClient."""
    # 1. GET /health
    r_health = client.get("/health")
    assert r_health.status_code == 200

    # 2. GET /traces
    r_traces = client.get("/traces")
    assert r_traces.status_code == 200
    traces = r_traces.json()
    assert len(traces) == 3

    # 3. GET /traces/{id} for all fixtures
    for t in traces:
        t_id = t["id"]
        r_get = client.get(f"/traces/{t_id}")
        assert r_get.status_code == 200
        assert r_get.json()["id"] == t_id

        # 4. POST /traces/{id}/diagnose
        r_diag = client.post(f"/traces/{t_id}/diagnose")
        assert r_diag.status_code == 200
        diag_data = r_diag.json()
        assert FullDiagnosisResponse.model_validate(diag_data)

        # 5. POST /traces/{id}/regression-test
        r_reg = client.post(f"/traces/{t_id}/regression-test")
        assert r_reg.status_code == 200
        reg_data = r_reg.json()
        assert RegressionTest.model_validate(reg_data)

    # 6. Check 404 behavior
    r_404 = client.get("/traces/invalid_id_999")
    assert r_404.status_code == 404

    print("[PASSED] API Endpoints Verification")


if __name__ == "__main__":
    verify_all_fixtures()
    verify_graph_generation()
    verify_anomaly_detection()
    verify_critical_path_and_backward_walk()
    verify_diagnosis_and_groundedness()
    verify_regression_generator()
    verify_api_endpoints()
    print("Full TraceMind Backend End-to-End Verification Complete: ALL CHECKS PASSED!")
