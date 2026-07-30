"""Unit tests for Groundedness Validation module."""

import sys
from pathlib import Path
import networkx as nx

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from diagnosis.validator import validate_groundedness
from models.trace import DiagnosisResult, SuggestedFix


def test_fully_grounded_diagnosis():
    g = nx.DiGraph()
    g.add_node("n1", type="plan")
    g.add_node("n2", type="tool_call")
    g.add_node("n3", type="observation")
    g.add_edge("n1", "n2")
    g.add_edge("n2", "n3")

    diag = DiagnosisResult(
        failure_category="Tool",
        confidence=0.90,
        root_cause_node_id="n2",
        evidence_node_ids=["n2", "n3"],
        explanation="Tool output was degraded.",
        suggested_fix=SuggestedFix(type="retry_policy", target="tool", diff="retry"),
        grounded=True,
    )

    validated = validate_groundedness(diag, g)
    assert validated.grounded is True
    assert validated.confidence == 0.90
    assert "WARNING" not in validated.explanation


def test_nonexistent_evidence_node_downgrades_confidence():
    g = nx.DiGraph()
    g.add_node("n1")
    g.add_node("n2")
    g.add_edge("n1", "n2")

    # LLM hallucinates evidence node 'n_hallucinated' which does NOT exist in g
    diag = DiagnosisResult(
        failure_category="Reasoning",
        confidence=0.85,
        root_cause_node_id="n1",
        evidence_node_ids=["n1", "n_hallucinated"],
        explanation="LLM cited a non-existent node.",
        suggested_fix=SuggestedFix(type="prompt_patch", target="prompt", diff="patch"),
        grounded=True,
    )

    validated = validate_groundedness(diag, g)
    assert validated.grounded is False
    assert validated.confidence == 0.65  # Downgraded from 0.85 by 0.20
    assert "WARNING: Grounding failed" in validated.explanation
    assert "n_hallucinated" in validated.explanation


def test_disconnected_evidence_node_downgrades_confidence():
    g = nx.DiGraph()
    # Subgraph 1
    g.add_node("n1")
    g.add_node("n2")
    g.add_edge("n1", "n2")

    # Disconnected Subgraph 2
    g.add_node("n_isolated")

    # LLM cites 'n_isolated' which is disconnected from root cause 'n1'
    diag = DiagnosisResult(
        failure_category="Coordination",
        confidence=0.80,
        root_cause_node_id="n1",
        evidence_node_ids=["n1", "n_isolated"],
        explanation="Disconnected evidence test.",
        suggested_fix=SuggestedFix(type="guardrail_addition", target="orchestrator", diff="add check"),
        grounded=True,
    )

    validated = validate_groundedness(diag, g)
    assert validated.grounded is False
    assert validated.confidence == 0.60  # Downgraded from 0.80 by 0.20
    assert "WARNING: Grounding failed" in validated.explanation


def test_nonexistent_root_cause_downgrades_confidence():
    g = nx.DiGraph()
    g.add_node("n1")

    diag = DiagnosisResult(
        failure_category="Planning",
        confidence=0.70,
        root_cause_node_id="n_missing",
        evidence_node_ids=["n1"],
        explanation="Missing root cause test.",
        suggested_fix=SuggestedFix(type="prompt_patch", target="plan", diff="fix"),
        grounded=True,
    )

    validated = validate_groundedness(diag, g)
    assert validated.grounded is False
    assert validated.confidence == 0.50  # Downgraded from 0.70 by 0.20


if __name__ == "__main__":
    test_fully_grounded_diagnosis()
    test_nonexistent_evidence_node_downgrades_confidence()
    test_disconnected_evidence_node_downgrades_confidence()
    test_nonexistent_root_cause_downgrades_confidence()
    print("All Groundedness Validation unit tests passed successfully!")
