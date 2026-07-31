"""
Unit tests for Agent 365 OTLP and Arize Phoenix Adapters.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Ensure sys.path includes backend and project root
backend_dir = Path(__file__).resolve().parent.parent
project_dir = backend_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

from agent365.adapters.otlp import load_otlp_trace_from_file
from agent365.adapters.phoenix import PhoenixAdapter


class TestAgent365Adapters:
    def test_load_otlp_file(self, tmp_path):
        trace_file = tmp_path / "trace.json"
        data = {
            "spans": [
                {"span_id": "s1", "trace_id": "t1", "name": "root_span"},
                {"span_id": "s2", "parent_span_id": "s1", "trace_id": "t1", "name": "child_span"},
            ]
        }
        trace_file.write_text(json.dumps(data), encoding="utf-8")

        spans = load_otlp_trace_from_file(trace_file)
        assert len(spans) == 2
        assert spans[0].span_id == "s1"
        assert spans[1].parent_span_id == "s1"

    def test_phoenix_adapter_fetch_and_annotate(self):
        adapter = PhoenixAdapter(phoenix_url="http://localhost:6006")

        mock_get_res = MagicMock()
        mock_get_res.status_code = 200
        mock_get_res.json.return_value = {
            "spans": [
                {"span_id": "sp_1", "trace_id": "tr_1", "name": "search_kb"},
            ]
        }

        mock_post_res = MagicMock()
        mock_post_res.status_code = 201

        with patch("requests.get", return_value=mock_get_res), patch("requests.post", return_value=mock_post_res):
            spans = adapter.fetch_trace_spans("tr_1")
            assert len(spans) == 1
            assert spans[0].span_id == "sp_1"

            ok = adapter.annotate_root_cause("tr_1", "sp_1", "Retrieval", 0.9, "Stale doc")
            assert ok is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
