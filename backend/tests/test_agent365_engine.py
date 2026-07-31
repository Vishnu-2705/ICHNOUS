"""
Integration tests for Agent 365 Causal Intelligence Engine on OTel Spans.
"""

import sys
from pathlib import Path
import pytest

# Ensure sys.path includes backend and project root
backend_dir = Path(__file__).resolve().parent.parent
project_dir = backend_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

from agent365.engine.analyzer import analyze_otel_trace
from models.trace import FullDiagnosisResponse


class TestAgent365Engine:
    def test_analyze_otel_retrieval_failure(self):
        otel_spans = [
            {
                "span_id": "span_1",
                "trace_id": "trace_r1",
                "name": "plan_step",
                "attributes": {"openinference.span.kind": "AGENT", "input.value": "Customer refund query"},
            },
            {
                "span_id": "span_2",
                "parent_span_id": "span_1",
                "trace_id": "trace_r1",
                "name": "search_knowledge_base",
                "attributes": {
                    "openinference.span.kind": "TOOL",
                    "tool.name": "search_knowledge_base",
                    "retrieval.relevance_score": 0.42,
                    "document_id": "policy-2023",
                    "note": "Stale refund policy retrieved",
                },
            },
            {
                "span_id": "span_3",
                "parent_span_id": "span_2",
                "trace_id": "trace_r1",
                "name": "reasoning_step",
                "attributes": {
                    "openinference.span.kind": "LLM",
                    "input.value": "Policy says 30 days. Purchase was 45 days ago. Deny.",
                },
            },
            {
                "span_id": "span_4",
                "parent_span_id": "span_3",
                "trace_id": "trace_r1",
                "name": "final_answer",
                "attributes": {
                    "openinference.span.kind": "CHAIN",
                    "output.value": "Deny refund request.",
                },
            },
        ]

        res = analyze_otel_trace(otel_spans)
        assert isinstance(res, FullDiagnosisResponse)
        assert res.diagnosis.failure_category == "Retrieval"
        assert res.diagnosis.root_cause_node_id == "span_2"
        assert res.diagnosis.grounded is True

    def test_analyze_otel_tool_failure(self):
        otel_spans = [
            {
                "span_id": "s1",
                "trace_id": "trace_t1",
                "name": "plan",
                "attributes": {"openinference.span.kind": "AGENT", "input.value": "Fix NPE"},
            },
            {
                "span_id": "s2",
                "parent_span_id": "s1",
                "trace_id": "trace_t1",
                "name": "lint_analyze",
                "attributes": {
                    "openinference.span.kind": "TOOL",
                    "tool.name": "lint_analyze",
                    "error": "rate_limit_degraded",
                    "response_truncated": True,
                },
            },
            {
                "span_id": "s3",
                "parent_span_id": "s2",
                "trace_id": "trace_t1",
                "name": "reasoning",
                "attributes": {"openinference.span.kind": "LLM", "output.value": "UserService looks clean"},
            },
            {
                "span_id": "s4",
                "parent_span_id": "s3",
                "trace_id": "trace_t1",
                "name": "final_answer",
                "attributes": {"openinference.span.kind": "CHAIN", "output.value": "Fix UserController"},
            },
        ]

        res = analyze_otel_trace(otel_spans)
        assert isinstance(res, FullDiagnosisResponse)
        assert res.diagnosis.failure_category == "Tool"
        assert res.diagnosis.root_cause_node_id == "s2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
