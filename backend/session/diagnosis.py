"""
Live Diagnosis Integration Engine for TraceMind Sessions.

Connects live TraceSession objects and NetworkX DiGraph structures to the
deterministic causal analysis engine and grounded LLM diagnosis pipeline:
1. Session to Trace conversion
2. Anomaly surfacing (detect_anomalies)
3. Critical path extraction (extract_critical_path)
4. Backward causal walk (backward_walk)
5. Grounded LLM / rule-based diagnosis (diagnose_with_llm)
6. Graph serialization matching AGENTS.md §10
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
import networkx as nx

try:
    from diagnosis.llm import diagnose_with_llm
    from graph.analyzer import (
        backward_walk,
        detect_anomalies,
        extract_critical_path,
    )
    from graph.builder import build_graph
    from models.session import TraceSession
    from models.trace import (
        AnomalyFlag,
        FullDiagnosisResponse,
        RootCauseCandidate,
        Trace,
    )
    from session.converter import session_to_trace
except ImportError:
    from backend.diagnosis.llm import diagnose_with_llm
    from backend.graph.analyzer import (
        backward_walk,
        detect_anomalies,
        extract_critical_path,
    )
    from backend.graph.builder import build_graph
    from backend.models.session import TraceSession
    from backend.models.trace import (
        AnomalyFlag,
        FullDiagnosisResponse,
        RootCauseCandidate,
        Trace,
    )
    from backend.session.converter import session_to_trace


def serialize_session_graph(
    g: nx.DiGraph,
    root_cause_id: str = "",
    evidence_ids: Optional[List[str]] = None,
    critical_path: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Serialize NetworkX session graph for API response matching AGENTS.md §10.
    Includes source/target, from/to, highlight flags, and anomaly info.
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


def diagnose_session(
    session: TraceSession, g: Optional[nx.DiGraph] = None
) -> FullDiagnosisResponse:
    """
    Run full causal diagnosis pipeline on a live TraceSession.

    Can be executed mid-session (on-demand) or upon session completion.
    """
    trace = session_to_trace(session)

    # Use provided graph or build from session trace
    graph = g if g is not None and g.number_of_nodes() > 0 else build_graph(trace)

    # 1. Surface anomalies
    anomalies = detect_anomalies(graph)

    # 2. Extract critical path
    critical_path = extract_critical_path(graph)

    # 3. Perform backward walk to locate root cause candidate
    candidate = backward_walk(graph, critical_path, anomalies)

    # 4. Gather evidence nodes
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

    # 5. Execute grounded LLM / fallback diagnosis
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


async def async_diagnose_session(
    session: TraceSession, g: Optional[nx.DiGraph] = None
) -> FullDiagnosisResponse:
    """
    Asynchronously run diagnose_session in a thread pool to avoid blocking the event loop.
    """
    return await asyncio.to_thread(diagnose_session, session, g)
