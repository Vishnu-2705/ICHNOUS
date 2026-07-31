"""
Unit tests for Agent 365 OpenTelemetry Span Models.
"""

import sys
from pathlib import Path
import pytest

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
project_dir = backend_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

from agent365.otel.models import (
    OpenInferenceSpanKind,
    OTelSpan,
    OTelSpanStatus,
    get_relevance_score,
    get_span_content,
    get_tool_name,
    is_span_truncated,
)


class TestAgent365OTelModels:
    def test_otlp_dict_parsing(self):
        data = {
            "span_id": "span_101",
            "parent_span_id": "span_100",
            "trace_id": "trace_999",
            "name": "search_knowledge_base",
            "duration_ms": 450.0,
            "status": {"code": "OK"},
            "attributes": {
                "openinference.span.kind": "TOOL",
                "tool.name": "search_knowledge_base",
                "retrieval.relevance_score": 0.42,
                "input.value": "search query for refund policy",
            },
        }
        span = OTelSpan.from_otlp_dict(data)
        assert span.span_id == "span_101"
        assert span.parent_span_id == "span_100"
        assert span.trace_id == "trace_999"
        assert span.kind == OpenInferenceSpanKind.TOOL
        assert span.status_code == OTelSpanStatus.OK
        assert get_tool_name(span) == "search_knowledge_base"
        assert get_relevance_score(span) == 0.42
        assert get_span_content(span) == "search query for refund policy"

    def test_otlp_key_value_attributes(self):
        data = {
            "spanId": "span_201",
            "traceId": "trace_888",
            "name": "llm_call",
            "attributes": [
                {"key": "openinference.span.kind", "value": {"stringValue": "LLM"}},
                {"key": "gen_ai.prompt", "value": {"stringValue": "Synthesize answer"}},
                {"key": "response_truncated", "value": {"boolValue": True}},
            ],
        }
        span = OTelSpan.from_otlp_dict(data)
        assert span.span_id == "span_201"
        assert span.kind == OpenInferenceSpanKind.LLM
        assert get_span_content(span) == "Synthesize answer"
        assert is_span_truncated(span) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
