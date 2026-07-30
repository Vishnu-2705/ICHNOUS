"""
Traces API routes module for TraceMind.
"""

import asyncio
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

# In-memory diagnosis and regression test caches per AGENTS.md (USE_CACHED_DIAGNOSES)
_DIAGNOSIS_CACHE: Dict[str, FullDiagnosisResponse] = {}
_REGRESSION_CACHE: Dict[str, RegressionTest] = {}


def _serialize_graph(
    g,
    root_cause_id: str = "",
    evidence_ids: List[str] = None,
    critical_path: List[str] = None,
) -> Dict[str, Any]:
    """
    Serialize graph elements for API response matching AGENTS.md §10.
    Includes both source/target and from/to, as well as boolean flags and string highlights.
    """
    evidence_set = set(evidence_ids or [])
    critical_set = set(critical_path or [])
    nodes_list = []
    for nid in g.nodes:
        data = g.nodes[nid]
        is_root = nid == root_cause_id
        is_evidence = nid in evidence_set
        is_critical = nid in critical_set
        highlight = (
            "root_cause"
            if is_root
            else "evidence"
            if is_evidence
            else "critical_path"
            if is_critical
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
                "is_root_cause": is_root,
                "is_evidence": is_evidence,
                "is_critical_path": is_critical,
            }
        )
    edges_list = []
    for src, dst in g.edges:
        is_evidence = src in evidence_set and dst in evidence_set
        is_critical = src in critical_set and dst in critical_set
        edges_list.append(
            {
                "source": src,
                "target": dst,
                "from": src,
                "to": dst,
                "highlight": "evidence" if is_evidence else "critical_path" if is_critical else "normal",
                "is_evidence": is_evidence,
                "is_critical_path": is_critical,
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
    Uses in-memory cache if available.
    """
    try:
        trace = load_fixture_trace(trace_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Trace '{trace_id}' not found.")

    if trace.id in _DIAGNOSIS_CACHE:
        return _DIAGNOSIS_CACHE[trace.id]

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

    # Offload synchronous LLM call to thread to prevent blocking event loop
    diagnosis_result = await asyncio.to_thread(
        diagnose_with_llm, root_cause_candidate, evidence_nodes, g=g
    )

    graph_data = _serialize_graph(
        g,
        root_cause_id=diagnosis_result.root_cause_node_id,
        evidence_ids=diagnosis_result.evidence_node_ids,
        critical_path=critical_path,
    )

    response = FullDiagnosisResponse(
        diagnosis=diagnosis_result,
        graph=graph_data,
        anomalies=anomalies,
        critical_path=critical_path,
    )
    _DIAGNOSIS_CACHE[trace.id] = response
    return response


@router.post("/{trace_id}/regression-test", response_model=RegressionTest)
async def generate_regression_test_endpoint(trace_id: str) -> RegressionTest:
    """
    POST /traces/{id}/regression-test
    Generates a regression test artifact for the specified trace.
    Uses in-memory cache if available.
    """
    try:
        trace = load_fixture_trace(trace_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Trace '{trace_id}' not found.")

    if trace.id in _REGRESSION_CACHE:
        return _REGRESSION_CACHE[trace.id]

    # Utilize cached diagnosis response if available to prevent duplicate LLM calls
    if trace.id in _DIAGNOSIS_CACHE:
        full_diag = _DIAGNOSIS_CACHE[trace.id]
        g = build_graph(trace)
        regression_test = generate_regression_test(trace, full_diag.diagnosis, g)
        _REGRESSION_CACHE[trace.id] = regression_test
        return regression_test

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

    diagnosis_result = await asyncio.to_thread(
        diagnose_with_llm, root_cause_candidate, evidence_nodes, g=g
    )
    regression_test = generate_regression_test(trace, diagnosis_result, g)
    _REGRESSION_CACHE[trace.id] = regression_test
    return regression_test
