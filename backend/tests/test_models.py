"""Tests for verifying TraceMind Pydantic models validation."""

import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from models.trace import (
    NodeType,
    TraceNode,
    Trace,
    TraceSummary,
    AnomalyFlag,
    RootCauseCandidate,
    SuggestedFix,
    DiagnosisResult,
    FullDiagnosisResponse,
    RegressionAssertion,
    RegressionTest,
)


def test_models_validation():
    # 1. NodeType
    assert NodeType.PLAN == "plan"

    # 2. TraceNode
    node = TraceNode(
        id="node-1",
        type=NodeType.TOOL_CALL,
        timestamp="2026-07-30T14:00:00Z",
        content="calling search tool",
        metadata={"key": "val"},
        reads_from=["node-0"],
    )
    assert node.id == "node-1"

    # 3. Trace
    trace = Trace(
        id="trace-1",
        name="Test Trace",
        description="A test trace",
        nodes=[node],
        expected_failure_category="tool_error",
    )
    assert trace.nodes[0].id == "node-1"

    # 4. TraceSummary
    summary = TraceSummary(
        id="trace-1",
        name="Test Trace",
        description="A test trace summary",
    )
    assert summary.id == "trace-1"

    # 5. AnomalyFlag
    anomaly = AnomalyFlag(
        node_id="node-1",
        anomaly_type="high_latency",
        details="Latency > 5s",
        severity_score=0.8,
    )
    assert anomaly.severity_score == 0.8

    # 6. RootCauseCandidate
    root_cause = RootCauseCandidate(
        node_id="node-1",
        divergence_score=0.95,
        evidence_node_ids=["node-0", "node-1"],
        critical_path=["node-0", "node-1"],
    )
    assert root_cause.divergence_score == 0.95

    # 7. SuggestedFix
    fix = SuggestedFix(
        type="prompt_patch",
        target="system_prompt",
        diff="--- old\n+++ new",
    )
    assert fix.type == "prompt_patch"

    # 8. DiagnosisResult
    diagnosis = DiagnosisResult(
        failure_category="prompt_error",
        confidence=0.9,
        root_cause_node_id="node-1",
        evidence_node_ids=["node-1"],
        explanation="Prompt failed to constrain JSON schema",
        suggested_fix=fix,
        grounded=True,
    )
    assert diagnosis.grounded is True

    # 9. FullDiagnosisResponse
    full_resp = FullDiagnosisResponse(
        diagnosis=diagnosis,
        graph={"nodes": [], "edges": []},
        anomalies=[anomaly],
        critical_path=["node-1"],
    )
    assert full_resp.diagnosis.confidence == 0.9

    # 10. RegressionAssertion
    assertion = RegressionAssertion(
        failure_category="prompt_error",
        root_cause_pattern="json_schema_error",
    )
    assert assertion.failure_category == "prompt_error"

    # 11. RegressionTest
    reg_test = RegressionTest(
        trace_id="trace-1",
        trace_name="Test Trace",
        failure_category="prompt_error",
        root_cause_node_id="node-1",
        minimal_inputs={"query": "test"},
        recorded_tool_outputs=[{"result": "ok"}],
        assertion=assertion,
    )
    assert reg_test.trace_id == "trace-1"

    print("All 11 Pydantic models validated successfully!")


if __name__ == "__main__":
    test_models_validation()
