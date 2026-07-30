"""Unit tests for LLM Diagnosis module."""

import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from diagnosis.llm import diagnose_with_llm
from diagnosis.taxonomy import TAXONOMY_LIST
from models.trace import DiagnosisResult, RootCauseCandidate, SuggestedFix


def test_diagnose_with_llm_valid_json():
    candidate = RootCauseCandidate(
        node_id="node_2",
        divergence_score=0.85,
        evidence_node_ids=["node_2", "node_3", "node_4"],
        critical_path=["node_1", "node_2", "node_3", "node_4"],
    )
    evidence_nodes = [
        {"id": "node_2", "type": "tool_call", "content": "search_knowledge_base()", "metadata": {"relevance_score": 0.42}},
        {"id": "node_3", "type": "observation", "content": "Stale refund policy 2023", "metadata": {}},
        {"id": "node_4", "type": "reasoning", "content": "Evaluating refund eligibility", "metadata": {}},
    ]

    valid_json_response = """
    {
      "failure_category": "Retrieval",
      "confidence": 0.95,
      "root_cause_node_id": "node_2",
      "evidence_node_ids": ["node_2", "node_3", "node_4"],
      "explanation": "The retrieval tool call pulled a stale 2023 policy instead of 2025.",
      "suggested_fix": {
        "type": "tool_schema_fix",
        "target": "knowledge_base_retriever",
        "diff": "Enforce document freshness filter date >= 2025."
      },
      "grounded": true
    }
    """

    call_count = 0

    def mock_llm(system: str, user: str) -> str:
        nonlocal call_count
        call_count += 1
        assert "Retrieval" in system or "Retrieval" in user
        assert "node_2" in user
        return valid_json_response

    result = diagnose_with_llm(
        candidate=candidate,
        evidence_nodes=evidence_nodes,
        taxonomy=TAXONOMY_LIST,
        llm_client=mock_llm,
    )

    assert isinstance(result, DiagnosisResult)
    assert result.failure_category == "Retrieval"
    assert result.confidence == 0.95
    assert result.root_cause_node_id == "node_2"
    assert result.suggested_fix.type == "tool_schema_fix"
    assert call_count == 1  # Exactly ONE successful call


def test_diagnose_with_llm_retry_on_malformed_json():
    candidate = RootCauseCandidate(
        node_id="node_5",
        divergence_score=0.75,
        evidence_node_ids=["node_5", "node_6"],
        critical_path=["node_1", "node_5", "node_6"],
    )
    evidence_nodes = [
        {"id": "node_5", "type": "tool_call", "content": "lint_analyze()"},
        {"id": "node_6", "type": "observation", "content": "Truncated output"},
    ]

    malformed_response = "Here is your diagnosis: { failure_category: Tool, INVALID JSON }"
    valid_json_response = """
    {
      "failure_category": "Tool",
      "confidence": 0.90,
      "root_cause_node_id": "node_5",
      "evidence_node_ids": ["node_5", "node_6"],
      "explanation": "Tool call returned truncated output due to rate limiting.",
      "suggested_fix": {
        "type": "retry_policy",
        "target": "lint_tool",
        "diff": "Retry with backoff."
      },
      "grounded": true
    }
    """

    call_count = 0

    def mock_llm(system: str, user: str) -> str:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return malformed_response  # Malformed JSON on 1st call
        return valid_json_response  # Valid JSON on 2nd call (retry)

    result = diagnose_with_llm(
        candidate=candidate,
        evidence_nodes=evidence_nodes,
        taxonomy=TAXONOMY_LIST,
        llm_client=mock_llm,
        max_retries=2,
    )

    assert isinstance(result, DiagnosisResult)
    assert result.failure_category == "Tool"
    assert call_count == 2  # Retried on malformed JSON and succeeded on 2nd call


def test_fallback_when_retries_exhausted():
    candidate = RootCauseCandidate(
        node_id="node_2",
        divergence_score=0.5,
        evidence_node_ids=["node_2"],
        critical_path=["node_1", "node_2"],
    )
    evidence_nodes = [
        {"id": "node_2", "type": "tool_call", "content": "search_knowledge_base('stale policy')", "metadata": {"tool_name": "search_knowledge_base"}},
    ]

    def broken_llm(system: str, user: str) -> str:
        return "ALWAYS INVALID NON-JSON"

    result = diagnose_with_llm(
        candidate=candidate,
        evidence_nodes=evidence_nodes,
        taxonomy=TAXONOMY_LIST,
        llm_client=broken_llm,
        max_retries=1,
    )

    assert isinstance(result, DiagnosisResult)
    assert result.root_cause_node_id == "node_2"
    assert result.failure_category == "Retrieval"


def test_fallback_diagnosis_taxonomy_mapping():
    # Test Tool fallback
    tool_candidate = RootCauseCandidate(node_id="node_5", divergence_score=0.6, evidence_node_ids=["node_5"], critical_path=["node_5"])
    tool_evidence = [{"id": "node_5", "type": "tool_call", "content": "lint_analyze()", "metadata": {"tool_name": "lint_analyze", "response_truncated": True}}]
    tool_result = diagnose_with_llm(tool_candidate, tool_evidence, taxonomy=TAXONOMY_LIST, llm_client=lambda s, u: "INVALID")
    assert tool_result.failure_category == "Tool"

    # Test Coordination fallback
    coord_candidate = RootCauseCandidate(node_id="node_3", divergence_score=0.7, evidence_node_ids=["node_3"], critical_path=["node_3"])
    coord_evidence = [{"id": "node_3", "type": "observation", "content": "Delegation loop timeout between ResearchAgent and AnalysisAgent", "metadata": {"error": "execution_timeout"}}]
    coord_result = diagnose_with_llm(coord_candidate, coord_evidence, taxonomy=TAXONOMY_LIST, llm_client=lambda s, u: "INVALID")
    assert coord_result.failure_category == "Coordination"


if __name__ == "__main__":
    test_diagnose_with_llm_valid_json()
    test_diagnose_with_llm_retry_on_malformed_json()
    test_fallback_when_retries_exhausted()
    test_fallback_diagnosis_taxonomy_mapping()
    print("All LLM Integration unit tests passed successfully!")
