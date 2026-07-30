"""
Groundedness Validator for TraceMind LLM Diagnoses.

Validates that all evidence nodes cited by an LLM diagnosis exist in the execution graph
and are structurally connected to the root cause node.
Downgrades confidence if any cited evidence is ungrounded.
"""

from __future__ import annotations

from typing import Optional
import networkx as nx

try:
    from models.trace import DiagnosisResult, RootCauseCandidate
except ImportError:
    from backend.models.trace import DiagnosisResult, RootCauseCandidate


def validate_groundedness(
    diagnosis: DiagnosisResult,
    g: nx.DiGraph,
    root_cause_node_id: Optional[str] = None,
    candidate: Optional[RootCauseCandidate] = None,
) -> DiagnosisResult:
    """
    Validate that an LLM-generated DiagnosisResult is grounded in the execution graph.

    Checks:
    1. The root cause node exists in the graph.
    2. Every cited evidence node in diagnosis.evidence_node_ids exists in g.nodes.
    3. Every cited evidence node is structurally connected to root_cause_node_id in g.

    If any validation check fails:
    - grounded is set to False
    - confidence score is downgraded (decreased by 0.20, minimum 0.10)
    - explanation receives a warning tag describing the ungrounded node/reason.

    Returns the validated DiagnosisResult.
    """
    if root_cause_node_id is None:
        if candidate and candidate.node_id:
            root_cause_node_id = candidate.node_id
        else:
            root_cause_node_id = diagnosis.root_cause_node_id

    valid_nodes = set(g.nodes)
    ungrounded_reason: Optional[str] = None

    # Check 1: Root cause node exists
    if root_cause_node_id and root_cause_node_id not in valid_nodes:
        ungrounded_reason = f"Root cause node '{root_cause_node_id}' does not exist in graph."

    # Check 2 & 3: Evidence nodes existence and connectivity
    if not ungrounded_reason and diagnosis.evidence_node_ids:
        undirected_g = g.to_undirected() if len(g.nodes) > 0 else None

        for cited_id in diagnosis.evidence_node_ids:
            # Check 2: Existence
            if cited_id not in valid_nodes:
                ungrounded_reason = f"Cited evidence node '{cited_id}' does not exist in execution graph."
                break

            # Check 3: Connectivity to root cause node
            if root_cause_node_id and root_cause_node_id in valid_nodes and cited_id != root_cause_node_id:
                try:
                    is_connected = (
                        nx.has_path(g, root_cause_node_id, cited_id)
                        or nx.has_path(g, cited_id, root_cause_node_id)
                        or (undirected_g and nx.has_path(undirected_g, root_cause_node_id, cited_id))
                    )
                except (nx.NetworkXError, nx.NodeNotFound):
                    is_connected = False

                if not is_connected:
                    ungrounded_reason = (
                        f"Cited evidence node '{cited_id}' is not connected to root cause '{root_cause_node_id}'."
                    )
                    break

    # If ungrounded, downgrade confidence and mark grounded=False
    if ungrounded_reason:
        new_confidence = max(0.10, round(diagnosis.confidence - 0.20, 2))
        warning_msg = f" [WARNING: Grounding failed - {ungrounded_reason}]"
        new_explanation = diagnosis.explanation
        if warning_msg not in new_explanation:
            new_explanation += warning_msg

        return DiagnosisResult(
            failure_category=diagnosis.failure_category,
            confidence=new_confidence,
            root_cause_node_id=diagnosis.root_cause_node_id,
            evidence_node_ids=diagnosis.evidence_node_ids,
            explanation=new_explanation,
            suggested_fix=diagnosis.suggested_fix,
            grounded=False,
        )

    # Fully grounded
    return DiagnosisResult(
        failure_category=diagnosis.failure_category,
        confidence=diagnosis.confidence,
        root_cause_node_id=diagnosis.root_cause_node_id,
        evidence_node_ids=diagnosis.evidence_node_ids,
        explanation=diagnosis.explanation,
        suggested_fix=diagnosis.suggested_fix,
        grounded=True,
    )
