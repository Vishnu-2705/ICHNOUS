"""
Unit tests for Agent 365 CLI.
"""

import json
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

from agent365.cli import main


class TestAgent365CLI:
    def test_cli_diagnose_otlp_file(self, tmp_path):
        trace_file = tmp_path / "otlp_trace.json"
        data = {
            "spans": [
                {
                    "span_id": "c1",
                    "trace_id": "cli_tr_1",
                    "name": "plan",
                    "attributes": {"openinference.span.kind": "AGENT", "input.value": "CLI query"},
                },
                {
                    "span_id": "c2",
                    "parent_span_id": "c1",
                    "trace_id": "cli_tr_1",
                    "name": "search_knowledge_base",
                    "attributes": {
                        "openinference.span.kind": "TOOL",
                        "tool.name": "search_knowledge_base",
                        "retrieval.relevance_score": 0.3,
                        "note": "stale doc",
                    },
                },
                {
                    "span_id": "c3",
                    "parent_span_id": "c2",
                    "trace_id": "cli_tr_1",
                    "name": "final_answer",
                    "attributes": {"openinference.span.kind": "CHAIN", "output.value": "Result"},
                },
            ]
        }
        trace_file.write_text(json.dumps(data), encoding="utf-8")

        code = main(["diagnose", "--otlp-file", str(trace_file)])
        assert code == 0

    def test_cli_export_regression(self, tmp_path):
        trace_file = tmp_path / "otlp_trace.json"
        out_file = tmp_path / "test_reg.py"
        data = {
            "spans": [
                {
                    "span_id": "c1",
                    "trace_id": "cli_tr_1",
                    "name": "plan",
                    "attributes": {"openinference.span.kind": "AGENT", "input.value": "CLI query"},
                },
                {
                    "span_id": "c2",
                    "parent_span_id": "c1",
                    "trace_id": "cli_tr_1",
                    "name": "search_knowledge_base",
                    "attributes": {
                        "openinference.span.kind": "TOOL",
                        "tool.name": "search_knowledge_base",
                        "retrieval.relevance_score": 0.3,
                        "note": "stale doc",
                    },
                },
                {
                    "span_id": "c3",
                    "parent_span_id": "c2",
                    "trace_id": "cli_tr_1",
                    "name": "final_answer",
                    "attributes": {"openinference.span.kind": "CHAIN", "output.value": "Result"},
                },
            ]
        }
        trace_file.write_text(json.dumps(data), encoding="utf-8")

        code = main(["export-regression", "--otlp-file", str(trace_file), "--output", str(out_file)])
        assert code == 0
        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        assert "def test_agent_regression_failure_isolation():" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
