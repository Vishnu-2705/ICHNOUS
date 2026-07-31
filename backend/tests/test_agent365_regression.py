"""
Unit tests for Agent 365 Pytest Regression Generator.
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
from agent365.engine.regression import generate_pytest_regression_script


class TestAgent365Regression:
    def test_generate_pytest_regression_script(self):
        otel_spans = [
            {
                "span_id": "sp_1",
                "trace_id": "tr_reg_1",
                "name": "plan",
                "attributes": {"openinference.span.kind": "AGENT", "input.value": "Process invoice"},
            },
            {
                "span_id": "sp_2",
                "parent_span_id": "sp_1",
                "trace_id": "tr_reg_1",
                "name": "search_knowledge_base",
                "attributes": {
                    "openinference.span.kind": "TOOL",
                    "tool.name": "search_knowledge_base",
                    "retrieval.relevance_score": 0.3,
                    "note": "stale policy document",
                },
            },
            {
                "span_id": "sp_3",
                "parent_span_id": "sp_2",
                "trace_id": "tr_reg_1",
                "name": "reasoning",
                "attributes": {
                    "openinference.span.kind": "LLM",
                    "input.value": "Invoice data stale. Deny.",
                },
            },
            {
                "span_id": "sp_4",
                "parent_span_id": "sp_3",
                "trace_id": "tr_reg_1",
                "name": "final_answer",
                "attributes": {
                    "openinference.span.kind": "CHAIN",
                    "output.value": "Deny invoice processing.",
                },
            },
        ]

        diagnosis = analyze_otel_trace(otel_spans)
        script = generate_pytest_regression_script(diagnosis, otel_spans)

        assert "import pytest" in script
        assert "EXPECTED_FAILURE_CATEGORY = \"Retrieval\"" in script
        assert "EXPECTED_ROOT_CAUSE_SPAN_ID = \"sp_2\"" in script
        assert "def test_agent_regression_failure_isolation():" in script


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
