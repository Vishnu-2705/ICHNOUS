"""
Causal Intelligence Engine for Agent 365.

Analyzes OpenTelemetry / OpenInference execution graphs to perform:
1. Dynamic OTel attribute anomaly detection
2. Critical path extraction & divergence scoring
3. Backward causal walk to locate root cause candidate
4. Evidence gathering & grounded diagnosis generation
5. AGENTS.md §10 graph serialization
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
import networkx as nx

try:
    from diagnosis.llm import diagnose_with_llm
    from graph.analyzer import (
        backward_walk,
        detect_anomalies,
        extract_critical_path,
    )
    from models.trace import FullDiagnosisResponse
    from session.diagnosis import serialize_session_graph
except ImportError:
    from backend.diagnosis.llm import diagnose_with_llm
    from backend.graph.analyzer import (
        backward_walk,
        detect_anomalies,
        extract_critical_path,
    )
    from backend.models.trace import FullDiagnosisResponse
    from backend.session.diagnosis import serialize_session_graph

from agent365.otel.models import OTelSpan
from agent365.otel.parser import build_digraph_from_otel_spans


def analyze_otel_trace(
    spans: List[Union[OTelSpan, Dict[str, Any]]],
    g: Optional[nx.DiGraph] = None,
) -> FullDiagnosisResponse:
    """
    Run full causal diagnosis on an OpenTelemetry trace span tree.
    """
    graph = g if g is not None and g.number_of_nodes() > 0 else build_digraph_from_otel_spans(spans)

    if graph.number_of_nodes() == 0:
        raise ValueError("Cannot perform causal diagnosis on an empty OTel trace graph.")

    # 1. Detect anomalies on OTel metadata
    anomalies = detect_anomalies(graph)

    # 2. Extract critical path
    critical_path = extract_critical_path(graph)

    # 3. Perform backward walk to select root cause candidate
    candidate = backward_walk(graph, critical_path, anomalies)

    # 4. Extract grounded evidence node list
    evidence_nodes = [
        {
            "id": nid,
            "type": graph.nodes[nid].get("type"),
            "content": graph.nodes[nid].get("content"),
            "metadata": graph.nodes[nid].get("metadata"),
        }
        for nid in candidate.evidence_node_ids
        if graph.has_node(nid)
    ]

    # 5. Synthesize grounded diagnosis & patch fix
    diagnosis_result = diagnose_with_llm(candidate, evidence_nodes, g=graph)

    # 6. Serialize graph matching AGENTS.md §10 schema
    serialized_graph = serialize_session_graph(
        graph,
        root_cause_id=diagnosis_result.root_cause_node_id,
        evidence_ids=diagnosis_result.evidence_node_ids,
        critical_path=critical_path,
    )

    return FullDiagnosisResponse(
        diagnosis=diagnosis_result,
        graph=serialized_graph,
        anomalies=anomalies,
        critical_path=critical_path,
    )
