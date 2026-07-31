"""
Unit tests for Agent 365 OpenTelemetry Span Tree Parser.
"""

import sys
from pathlib import Path
import pytest
import networkx as nx

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
project_dir = backend_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

from agent365.otel.models import OpenInferenceSpanKind, OTelSpan
from agent365.otel.parser import build_digraph_from_otel_spans, map_span_kind_to_node_type
from models.trace import NodeType


class TestAgent365OTelParser:
    def test_build_digraph_from_span_tree(self):
        spans = [
            {
                "span_id": "span_root",
                "trace_id": "t1",
                "name": "agent_plan",
                "attributes": {"openinference.span.kind": "AGENT", "input.value": "Plan task"},
            },
            {
                "span_id": "span_tool",
                "parent_span_id": "span_root",
                "trace_id": "t1",
                "name": "search_kb",
                "attributes": {
                    "openinference.span.kind": "TOOL",
                    "tool.name": "search_kb",
                    "retrieval.relevance_score": 0.35,
                },
            },
            {
                "span_id": "span_llm",
                "parent_span_id": "span_tool",
                "trace_id": "t1",
                "name": "reasoning_step",
                "attributes": {"openinference.span.kind": "LLM", "output.value": "Deny refund"},
            },
        ]

        g = build_digraph_from_otel_spans(spans)
        assert isinstance(g, nx.DiGraph)
        assert g.number_of_nodes() == 3
        assert g.number_of_edges() == 2

        assert g.has_edge("span_root", "span_tool")
        assert g.has_edge("span_tool", "span_llm")

        # Verify metadata extraction
        tool_data = g.nodes["span_tool"]
        assert tool_data["type"] == NodeType.TOOL_CALL.value
        assert tool_data["metadata"]["tool_name"] == "search_kb"
        assert tool_data["metadata"]["relevance_score"] == 0.35


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
