"""
Traces API routes module for TraceMind.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException

try:
    from diagnosis.llm import diagnose_with_llm
    from fixtures import get_all_fixtures, load_fixture_trace
    from graph.analyzer import (
        backward_walk,
        detect_anomalies,
        extract_critical_path,
    )
    from graph.builder import build_graph
    from models.trace import (
        FullDiagnosisResponse,
        RegressionTest,
        Trace,
        TraceSummary,
    )
    from regression.generator import generate_regression_test
except ImportError:
    from backend.diagnosis.llm import diagnose_with_llm
    from backend.fixtures import get_all_fixtures, load_fixture_trace
    from backend.graph.analyzer import (
        backward_walk,
        detect_anomalies,
        extract_critical_path,
    )
    from backend.graph.builder import build_graph
    from backend.models.trace import (
        FullDiagnosisResponse,
        RegressionTest,
        Trace,
        TraceSummary,
    )
    from backend.regression.generator import generate_regression_test

router = APIRouter(prefix="/traces", tags=["traces"])


def _serialize_graph(
    g,
    root_cause_id: str = "",
    evidence_ids: List[str] = None,
    critical_path: List[str] = None,
) -> Dict[str, Any]:
    evidence_set = set(evidence_ids or [])
    critical_set = set(critical_path or [])
    nodes_list = []
    for nid in g.nodes:
        data = g.nodes[nid]
        highlight = (
            "root_cause"
            if nid == root_cause_id
            else "evidence"
            if nid in evidence_set
            else "critical_path"
            if nid in critical_set
            else "normal"
        )
        nodes_list.append(
            {
                "id": nid,
                "type": data.get("type", "unknown"),
                "content": data.get("content", ""),
                "metadata": data.get("metadata", {}),
                "timestamp": data.get("timestamp", ""),
                "highlight": highlight,
            }
        )
    edges_list = []
    for src, dst in g.edges:
        is_evidence = src in evidence_set and dst in evidence_set
        is_critical = src in critical_set and dst in critical_set
        edges_list.append(
            {
                "from": src,
                "to": dst,
                "highlight": "evidence" if is_evidence else "critical_path" if is_critical else "normal",
            }
        )
    return {"nodes": nodes_list, "edges": edges_list}


@router.get("", response_model=List[TraceSummary])
@router.get("/", response_model=List[TraceSummary])
async def list_traces() -> List[TraceSummary]:
    """
    GET /traces
    Returns a list of available trace summaries.
    """
    fixtures = get_all_fixtures()
    summaries = []
    for key, trace in fixtures.items():
        summaries.append(
            TraceSummary(
                id=trace.id,
                name=trace.name,
                description=trace.description,
            )
        )
    return summaries


@router.get("/{trace_id}", response_model=Trace)
async def get_trace(trace_id: str) -> Trace:
    """
    GET /traces/{id}
    Returns full trace details by ID. Raises 404 if not found.
    """
    try:
        trace = load_fixture_trace(trace_id)
        return trace
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Trace '{trace_id}' not found.")


@router.post("/{trace_id}/diagnose", response_model=FullDiagnosisResponse)
async def diagnose_trace(trace_id: str) -> FullDiagnosisResponse:
    """
    POST /traces/{id}/diagnose
    Runs causal graph construction, anomaly detection, backward causal walk,
    and LLM/rule-based diagnosis, returning FullDiagnosisResponse.
    """
    try:
        trace = load_fixture_trace(trace_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Trace '{trace_id}' not found.")

    g = build_graph(trace)
    anomalies = detect_anomalies(g)
    critical_path = extract_critical_path(g)
    root_cause_candidate = backward_walk(g, critical_path, anomalies)

    evidence_nodes = [
        {
            "id": nid,
            "type": g.nodes[nid].get("type"),
            "content": g.nodes[nid].get("content"),
            "metadata": g.nodes[nid].get("metadata"),
        }
        for nid in root_cause_candidate.evidence_node_ids
        if g.has_node(nid)
    ]

    diagnosis_result = diagnose_with_llm(root_cause_candidate, evidence_nodes, g=g)

    graph_data = _serialize_graph(
        g,
        root_cause_id=diagnosis_result.root_cause_node_id,
        evidence_ids=diagnosis_result.evidence_node_ids,
        critical_path=critical_path,
    )

    return FullDiagnosisResponse(
        diagnosis=diagnosis_result,
        graph=graph_data,
        anomalies=anomalies,
        critical_path=critical_path,
    )


@router.post("/{trace_id}/regression-test", response_model=RegressionTest)
async def generate_regression_test_endpoint(trace_id: str) -> RegressionTest:
    """
    POST /traces/{id}/regression-test
    Generates a regression test artifact for the specified trace.
    """
    try:
        trace = load_fixture_trace(trace_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Trace '{trace_id}' not found.")

    g = build_graph(trace)
    anomalies = detect_anomalies(g)
    critical_path = extract_critical_path(g)
    root_cause_candidate = backward_walk(g, critical_path, anomalies)

    evidence_nodes = [
        {
            "id": nid,
            "type": g.nodes[nid].get("type"),
            "content": g.nodes[nid].get("content"),
            "metadata": g.nodes[nid].get("metadata"),
        }
        for nid in root_cause_candidate.evidence_node_ids
        if g.has_node(nid)
    ]

    diagnosis_result = diagnose_with_llm(root_cause_candidate, evidence_nodes, g=g)
    regression_test = generate_regression_test(trace, diagnosis_result, g)
    return regression_test
