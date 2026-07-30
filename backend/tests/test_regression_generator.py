"""Unit tests for Regression Artifact Generator module."""

import json
import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fixtures import get_retrieval_failure_trace
from graph.analyzer import backward_walk, detect_anomalies, extract_critical_path
from graph.builder import build_graph
from models.trace import (
    DiagnosisResult,
    RegressionAssertion,
    RegressionTest,
    SuggestedFix,
)
from regression.generator import (
    generate_regression_test,
    generate_regression_test_dict,
    generate_regression_test_json,
)


def test_generate_regression_test_basic():
    trace = get_retrieval_failure_trace()
    g = build_graph(trace)
    anomalies = detect_anomalies(g)
    cp = extract_critical_path(g)
    rc = backward_walk(g, cp, anomalies)

    diagnosis = DiagnosisResult(
        failure_category="Retrieval",
        confidence=0.92,
        root_cause_node_id=rc.node_id,
        evidence_node_ids=rc.evidence_node_ids,
        explanation="Stale 2023 refund policy retrieved instead of 2025 policy.",
        suggested_fix=SuggestedFix(
            type="tool_schema_fix",
            target="knowledge_base_retriever",
            diff="Enforce document freshness filter date >= 2025.",
        ),
        grounded=True,
    )

    reg_test = generate_regression_test(trace, diagnosis, g)

    # 1. Verification of RegressionTest model structure
    assert isinstance(reg_test, RegressionTest)
    assert reg_test.trace_id == "trace_retrieval"
    assert reg_test.trace_name == "Retrieval Failure — Stale Refund Policy"
    assert reg_test.failure_category == "Retrieval"
    assert reg_test.root_cause_node_id == "node_2"

    # 2. Minimal inputs check
    assert "initial_task" in reg_test.minimal_inputs
    assert len(reg_test.minimal_inputs["initial_task"]) > 0

    # 3. Tool outputs check
    assert isinstance(reg_test.recorded_tool_outputs, list)
    assert len(reg_test.recorded_tool_outputs) > 0
    first_tool_out = reg_test.recorded_tool_outputs[0]
    assert "node_id" in first_tool_out
    assert "type" in first_tool_out
    assert "content" in first_tool_out

    # 4. Assertion check
    assert isinstance(reg_test.assertion, RegressionAssertion)
    assert reg_test.assertion.failure_category == "Retrieval"
    assert "node_2" in reg_test.assertion.root_cause_pattern


def test_generate_regression_test_json():
    trace = get_retrieval_failure_trace()
    diagnosis = DiagnosisResult(
        failure_category="Retrieval",
        confidence=0.9,
        root_cause_node_id="node_2",
        evidence_node_ids=["node_2", "node_3"],
        explanation="Stale document retrieved",
        suggested_fix=SuggestedFix(type="prompt_patch", target="search", diff="fix"),
        grounded=True,
    )

    json_str = generate_regression_test_json(trace, diagnosis)
    assert isinstance(json_str, str)

    # Validate JSON parsing
    parsed_dict = json.loads(json_str)
    assert parsed_dict["trace_id"] == "trace_retrieval"
    assert parsed_dict["failure_category"] == "Retrieval"
    assert parsed_dict["root_cause_node_id"] == "node_2"
    assert "initial_task" in parsed_dict["minimal_inputs"]
    assert "recorded_tool_outputs" in parsed_dict
    assert "assertion" in parsed_dict


def test_generate_regression_test_dict():
    trace = get_retrieval_failure_trace()
    diagnosis = DiagnosisResult(
        failure_category="Retrieval",
        confidence=0.9,
        root_cause_node_id="node_2",
        evidence_node_ids=["node_2"],
        explanation="Stale document",
        suggested_fix=SuggestedFix(type="prompt_patch", target="search", diff="fix"),
        grounded=True,
    )

    res_dict = generate_regression_test_dict(trace, diagnosis)
    assert isinstance(res_dict, dict)
    assert res_dict["trace_id"] == "trace_retrieval"


if __name__ == "__main__":
    test_generate_regression_test_basic()
    test_generate_regression_test_json()
    test_generate_regression_test_dict()
    print("All Regression Generator unit tests passed successfully!")
