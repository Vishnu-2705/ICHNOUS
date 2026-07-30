"""Unit tests for Root Cause Ranking module."""

import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from graph.analyzer import rank_root_cause_candidates, sort_root_cause_candidates
from models.trace import RootCauseCandidate


def test_ranking_by_divergence_score():
    cp = ["n0", "n1", "n2", "n3", "n4"]

    c1 = RootCauseCandidate(
        node_id="n1",
        divergence_score=0.4,
        evidence_node_ids=["n1", "n2", "n3", "n4"],
        critical_path=cp,
    )
    c2 = RootCauseCandidate(
        node_id="n2",
        divergence_score=0.8,
        evidence_node_ids=["n2", "n3", "n4"],
        critical_path=cp,
    )
    c3 = RootCauseCandidate(
        node_id="n3",
        divergence_score=0.2,
        evidence_node_ids=["n3", "n4"],
        critical_path=cp,
    )

    candidates = [c1, c3, c2]

    # Primary sort by divergence score: c2 (0.8) > c1 (0.4) > c3 (0.2)
    top_candidate = rank_root_cause_candidates(candidates)
    assert top_candidate is not None
    assert top_candidate.node_id == "n2"
    assert top_candidate.divergence_score == 0.8

    sorted_list = sort_root_cause_candidates(candidates)
    assert [c.node_id for c in sorted_list] == ["n2", "n1", "n3"]


def test_ranking_tie_breaking_by_causal_proximity():
    """
    When divergence scores are equal, the candidate with higher causal proximity
    (more upstream / earlier in critical_path) should rank higher.
    """
    cp = ["n0", "n1", "n2", "n3", "n4"]

    # Both c_downstream and c_upstream have equal divergence score = 0.5
    c_downstream = RootCauseCandidate(
        node_id="n3",  # Closer to failure (causal proximity = 1)
        divergence_score=0.5,
        evidence_node_ids=["n3", "n4"],
        critical_path=cp,
    )
    c_upstream = RootCauseCandidate(
        node_id="n1",  # Further upstream / earlier (causal proximity = 3)
        divergence_score=0.5,
        evidence_node_ids=["n1", "n2", "n3", "n4"],
        critical_path=cp,
    )

    candidates = [c_downstream, c_upstream]

    # Tie breaker must pick c_upstream (n1) over c_downstream (n3)
    top_candidate = rank_root_cause_candidates(candidates)
    assert top_candidate is not None
    assert top_candidate.node_id == "n1"


def test_empty_candidates_list():
    assert rank_root_cause_candidates([]) is None
    assert sort_root_cause_candidates([]) == []


if __name__ == "__main__":
    test_ranking_by_divergence_score()
    test_ranking_tie_breaking_by_causal_proximity()
    test_empty_candidates_list()
    print("All Root Cause Ranking unit tests passed successfully!")
