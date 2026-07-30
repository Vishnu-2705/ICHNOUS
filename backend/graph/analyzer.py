"""
Graph Analyzer module for TraceMind.

Implements deterministic anomaly detection, critical path extraction,
backward causal walk algorithm, and root cause candidate ranking on networkx.DiGraph.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import networkx as nx

try:
    from models.trace import AnomalyFlag, RootCauseCandidate
except ImportError:
    from backend.models.trace import AnomalyFlag, RootCauseCandidate

# ---------------------------------------------------------------------------
# Deterministic Thresholds
# ---------------------------------------------------------------------------
LATENCY_THRESHOLD_MS = 5000
RELEVANCE_THRESHOLD = 0.6
LARGE_RESPONSE_CHAR_THRESHOLD = 1000
DIVERGENCE_THRESHOLD = 0.4
NORMAL_THRESHOLD = 0.3


def detect_anomalies(g: nx.DiGraph) -> List[AnomalyFlag]:
    """
    Detect anomalies in a trace graph based on deterministic rules and thresholds.

    Anomaly types detected:
    - high_latency: node latency exceeds LATENCY_THRESHOLD_MS
    - tool_error: tool call produced an error
    - low_relevance: retrieval relevance score below RELEVANCE_THRESHOLD
    - cycle: node participates in a directed cycle
    - timeout: execution timed out
    - large_response: response size exceeds threshold or response was truncated
    """
    anomalies: List[AnomalyFlag] = []

    # Detect graph cycles
    cycle_nodes: set[str] = set()
    try:
        for cycle in nx.simple_cycles(g):
            if len(cycle) >= 1:
                for node_id in cycle:
                    cycle_nodes.add(node_id)
    except Exception:
        pass

    for node_id in g.nodes:
        node_data = g.nodes[node_id]
        meta = node_data.get("metadata", {})

        # 1. High Latency
        latency = meta.get("latency_ms", 0)
        if latency > LATENCY_THRESHOLD_MS:
            anomalies.append(
                AnomalyFlag(
                    node_id=node_id,
                    anomaly_type="high_latency",
                    details=f"Latency {latency}ms exceeds threshold {LATENCY_THRESHOLD_MS}ms",
                    severity_score=0.3,
                )
            )

        # 2. Tool Error
        error = meta.get("error")
        if error and error != "execution_timeout":
            anomalies.append(
                AnomalyFlag(
                    node_id=node_id,
                    anomaly_type="tool_error",
                    details=f"Tool error: {error}",
                    severity_score=0.5,
                )
            )

        # 3. Low Retrieval Relevance
        relevance = meta.get("relevance_score")
        if relevance is not None and relevance < RELEVANCE_THRESHOLD:
            anomalies.append(
                AnomalyFlag(
                    node_id=node_id,
                    anomaly_type="low_relevance",
                    details=f"Relevance score {relevance:.2f} below threshold {RELEVANCE_THRESHOLD}",
                    severity_score=0.4,
                )
            )

        # 4. Cycle Detection
        if node_id in cycle_nodes or meta.get("cycle_iteration") or meta.get("cycle_detected"):
            iteration = meta.get("cycle_iteration", 1)
            anomalies.append(
                AnomalyFlag(
                    node_id=node_id,
                    anomaly_type="cycle",
                    details=f"Node participates in a delegation cycle (iteration {iteration})",
                    severity_score=0.5,
                )
            )

        # 5. Timeout
        if meta.get("error") == "execution_timeout" or "timeout" in str(meta.get("error", "")).lower():
            anomalies.append(
                AnomalyFlag(
                    node_id=node_id,
                    anomaly_type="timeout",
                    details="Execution timed out without producing a final answer",
                    severity_score=0.5,
                )
            )

        # 6. Large Response / Truncated Output / Schema Mismatch
        char_count = meta.get("char_count", 0)
        if meta.get("response_truncated") or char_count > LARGE_RESPONSE_CHAR_THRESHOLD:
            completeness = meta.get("response_completeness")
            details = (
                f"Response truncated at {completeness:.0%} completeness"
                if completeness is not None
                else f"Response length ({char_count} chars) exceeds threshold or was truncated"
            )
            anomalies.append(
                AnomalyFlag(
                    node_id=node_id,
                    anomaly_type="large_response",
                    details=details,
                    severity_score=0.4,
                )
            )

        # 7. Dangling Reads From References
        if meta.get("dangling_reads_from"):
            dangling = ", ".join(meta["dangling_reads_from"])
            anomalies.append(
                AnomalyFlag(
                    node_id=node_id,
                    anomaly_type="dangling_reference",
                    details=f"Node references unresolvable reads_from ID(s): {dangling}",
                    severity_score=0.6,
                )
            )

    return anomalies


surface_anomalies = detect_anomalies


def find_failure_node(g: nx.DiGraph) -> str:
    """
    Identify the failure or terminus node in the execution graph.

    Prioritizes:
    1. Timeout node (error=='execution_timeout' or 'timeout' in error).
    2. Final Answer node (type=='final_answer').
    3. Fallback: Last node in graph node order.
    """
    if not g.nodes:
        return ""

    # Priority 1: Timeout node
    for nid in g.nodes:
        meta = g.nodes[nid].get("metadata", {})
        err = str(meta.get("error", "")).lower()
        if err == "execution_timeout" or "timeout" in err:
            return nid

    # Priority 2: Final answer node
    for nid in g.nodes:
        ntype = str(g.nodes[nid].get("type", "")).lower()
        if ntype == "final_answer":
            return nid

    # Fallback: Last node in graph
    return list(g.nodes)[-1]


def extract_critical_path(g: nx.DiGraph, failure_node_id: Optional[str] = None) -> List[str]:
    """
    Extract an ordered list of node IDs on the critical path from start (root) to failure.

    Handles graphs with cycles safely.
    """
    if not g.nodes:
        return []

    if failure_node_id is None or not g.has_node(failure_node_id):
        failure_node_id = find_failure_node(g)

    if not failure_node_id or not g.has_node(failure_node_id):
        return list(g.nodes)

    # Identify root node(s) (in-degree == 0)
    roots = [n for n in g.nodes if g.in_degree(n) == 0]
    if not roots:
        roots = [list(g.nodes)[0]]

    best_path: List[str] = []

    for root in roots:
        if root == failure_node_id:
            return [root]

        try:
            if nx.is_directed_acyclic_graph(g):
                # DAG: find all simple paths and pick the longest path
                for path in nx.all_simple_paths(g, root, failure_node_id):
                    if len(path) > len(best_path):
                        best_path = list(path)
            else:
                # Cyclic graph: use shortest path to safely prevent cycle loops
                path = nx.shortest_path(g, root, failure_node_id)
                if len(path) > len(best_path):
                    best_path = list(path)
        except (nx.NetworkXError, nx.NetworkXNoPath, nx.NodeNotFound):
            continue

    if not best_path:
        for root in roots:
            try:
                best_path = list(nx.shortest_path(g, root, failure_node_id))
                break
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

    if not best_path:
        best_path = list(g.nodes)

    return best_path


def compute_divergence(
    g: nx.DiGraph,
    node_id: str,
    anomalies: Optional[List[AnomalyFlag]] = None,
) -> float:
    """
    Compute divergence score (0.0 to 1.0) for a node using:
    - retrieval relevance (< 0.6)
    - tool errors
    - latency (> 5000ms)
    - cycle detection
    - schema mismatch
    - response truncation / low completeness
    """
    if not g.has_node(node_id):
        return 0.0

    score = 0.0
    meta = g.nodes[node_id].get("metadata", {})

    # 1. Retrieval Relevance
    relevance = meta.get("relevance_score")
    if relevance is not None and relevance < RELEVANCE_THRESHOLD:
        score += 0.4

    # 2. Tool Errors
    error = meta.get("error")
    if error and error != "execution_timeout":
        score += 0.5

    # 3. Latency
    latency = meta.get("latency_ms", 0)
    if latency > LATENCY_THRESHOLD_MS:
        score += 0.3

    # 4. Cycle Detection
    if meta.get("cycle_iteration") or meta.get("cycle_detected"):
        score += 0.5
    elif anomalies:
        for a in anomalies:
            if a.node_id == node_id and a.anomaly_type == "cycle":
                score += 0.5
                break

    # 5. Schema Mismatch
    err_str = str(meta.get("error", "")).lower()
    note_str = str(meta.get("note", "")).lower()
    if meta.get("schema_mismatch") or "schema" in err_str or "schema" in note_str:
        score += 0.5

    # Response truncation / completeness
    if meta.get("response_truncated"):
        score += 0.4

    completeness = meta.get("completeness")
    if completeness is not None and completeness < 0.5:
        score += 0.3

    return min(score, 1.0)


def _extract_evidence(g: nx.DiGraph, root_cause_id: str, critical_path: List[str]) -> List[str]:
    """Return root cause node ID + all downstream nodes on critical path leading to failure."""
    evidence: List[str] = []
    started = False
    for nid in critical_path:
        if nid == root_cause_id:
            started = True
        if started:
            evidence.append(nid)
    if not evidence and root_cause_id:
        evidence = [root_cause_id]
    return evidence


def backward_walk(
    g: nx.DiGraph,
    critical_path: Optional[List[str]] = None,
    anomalies: Optional[List[AnomalyFlag]] = None,
) -> RootCauseCandidate:
    """
    Walk backward from the failure node along the critical path to find the EARLIEST
    meaningful divergence (root cause).

    Chooses the earliest upstream node where divergence occurs and downstream nodes
    propagate the error cascade per AGENTS.md §8.4.
    """
    if not g.nodes:
        return RootCauseCandidate(
            node_id="",
            divergence_score=0.0,
            evidence_node_ids=[],
            critical_path=[],
        )

    if critical_path is None or not critical_path:
        critical_path = extract_critical_path(g)

    if anomalies is None:
        anomalies = detect_anomalies(g)

    # Compute divergence score for every node on the critical path
    divergences: Dict[str, float] = {}
    for nid in critical_path:
        divergences[nid] = compute_divergence(g, nid, anomalies)

    # Candidates: (node_id, divergence_score, causal_distance, downstream_normal)
    candidates: List[Tuple[str, float, int, bool]] = []

    # Iterate through critical path (excluding the failure node itself)
    for idx in range(len(critical_path) - 1):
        nid = critical_path[idx]
        div = divergences[nid]

        if div >= DIVERGENCE_THRESHOLD:
            # Check if downstream nodes are propagating (reasoning/observation propagation)
            downstream_normal = True
            for downstream_idx in range(idx + 1, len(critical_path) - 1):
                downstream_nid = critical_path[downstream_idx]
                # If a downstream node introduces a whole new independent error, downstream_normal is False
                if divergences[downstream_nid] > DIVERGENCE_THRESHOLD + 0.3:
                    downstream_normal = False
                    break

            # Distance from failure (higher = more upstream = earliest divergence)
            causal_distance = len(critical_path) - 1 - idx
            candidates.append((nid, div, causal_distance, downstream_normal))

    if not candidates:
        # Fallback: pick node with highest divergence that isn't failure node
        scored = [
            (nid, divergences[nid], len(critical_path) - 1 - i, True)
            for i, nid in enumerate(critical_path[:-1])
            if divergences[nid] > 0
        ]
        if scored:
            candidates = scored
        else:
            # Absolute fallback: first node on critical path
            candidates = [(critical_path[0], 0.0, len(critical_path) - 1, True)]

    # Rank per AGENTS.md §8.4:
    # 1. Prefer downstream_normal == True (propagation cascade)
    # 2. Prefer earliest upstream divergence (highest causal_distance) for equal or primary divergence
    # 3. Primary divergence score
    def ranking_key(item: Tuple[str, float, int, bool]):
        nid, div_score, causal_dist, is_downstream_normal = item
        # If it's the cycle origin or primary divergence, upstream position is primary
        is_cycle_origin = any(
            a.node_id == nid and a.anomaly_type == "cycle" for a in anomalies
        )
        if is_cycle_origin:
            return (2.0, causal_dist, div_score)
        return (1.0 if is_downstream_normal else 0.0, div_score, causal_dist)

    candidates.sort(key=ranking_key, reverse=True)
    best_id, best_div, _, _ = candidates[0]

    evidence_ids = _extract_evidence(g, best_id, critical_path)

    return RootCauseCandidate(
        node_id=best_id,
        divergence_score=best_div,
        evidence_node_ids=evidence_ids,
        critical_path=critical_path,
    )


# ---------------------------------------------------------------------------
# Root Cause Ranking
# ---------------------------------------------------------------------------
def sort_root_cause_candidates(candidates: List[RootCauseCandidate]) -> List[RootCauseCandidate]:
    """
    Sort a list of RootCauseCandidate objects by:
    1. Divergence score (descending - primary)
    2. Causal proximity / upstream position (descending - secondary: earlier in critical_path = higher priority)

    Returns the sorted list of candidates.
    """
    if not candidates:
        return []

    def get_sort_key(c: RootCauseCandidate) -> Tuple[float, int]:
        div_score = c.divergence_score

        # Calculate causal proximity (upstream distance from failure point)
        if c.critical_path and c.node_id in c.critical_path:
            idx = c.critical_path.index(c.node_id)
            causal_proximity = len(c.critical_path) - 1 - idx
        else:
            causal_proximity = len(c.evidence_node_ids)

        return (div_score, causal_proximity)

    return sorted(candidates, key=get_sort_key, reverse=True)


def rank_root_cause_candidates(candidates: List[RootCauseCandidate]) -> Optional[RootCauseCandidate]:
    """
    Rank root cause candidates and return the single highest-ranked candidate,
    or None if the candidates list is empty.
    """
    sorted_candidates = sort_root_cause_candidates(candidates)
    return sorted_candidates[0] if sorted_candidates else None
