"""
OpenTelemetry Span Tree to NetworkX DiGraph Parser for Agent 365.

Converts standard OpenTelemetry / OpenInference span trees into a Directed Acyclic
Graph (DiGraph) preserving parent-child relationships and data dependencies.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
import networkx as nx

try:
    from models.trace import NodeType
except ImportError:
    from backend.models.trace import NodeType

from agent365.otel.models import (
    OpenInferenceSpanKind,
    OTelSpan,
    OTelSpanStatus,
    get_relevance_score,
    get_span_content,
    get_tool_name,
    is_span_truncated,
)


def map_span_kind_to_node_type(span: OTelSpan) -> NodeType:
    """
    Map an OpenTelemetry/OpenInference span to an internal NodeType.
    """
    attrs = span.attributes
    kind = span.kind

    if kind == OpenInferenceSpanKind.TOOL:
        return NodeType.TOOL_CALL
    if kind in (OpenInferenceSpanKind.RETRIEVER, OpenInferenceSpanKind.RAG):
        return NodeType.TOOL_CALL
    if kind == OpenInferenceSpanKind.AGENT:
        return NodeType.DELEGATION if span.parent_span_id else NodeType.PLAN
    if kind == OpenInferenceSpanKind.LLM:
        # Check if LLM call is producing a tool call or reasoning
        if "gen_ai.completion" in attrs or "output.value" in attrs:
            content = get_span_content(span).lower()
            if "decision" in content or "approve" in content or "deny" in content:
                return NodeType.DECISION
            if "plan" in content:
                return NodeType.PLAN
        return NodeType.REASONING

    # Name-based heuristic fallbacks
    name_lower = span.name.lower()
    if "tool" in name_lower or "search" in name_lower or "query" in name_lower:
        return NodeType.TOOL_CALL
    if "plan" in name_lower:
        return NodeType.PLAN
    if "delegate" in name_lower:
        return NodeType.DELEGATION
    if "answer" in name_lower or "final" in name_lower:
        return NodeType.FINAL_ANSWER

    return NodeType.OBSERVATION


def build_digraph_from_otel_spans(spans: List[Union[OTelSpan, Dict[str, Any]]]) -> nx.DiGraph:
    """
    Convert a list of OTelSpan objects (or OTLP dicts) into a NetworkX DiGraph.

    Edges are drawn from parent spans to child spans (parent -> child), and
    dependency references (`reads_from`) are preserved.
    """
    parsed_spans: List[OTelSpan] = [
        s if isinstance(s, OTelSpan) else OTelSpan.from_otlp_dict(s)
        for s in spans
    ]

    g = nx.DiGraph()
    if not parsed_spans:
        return g

    # Trace ID from first span
    g.graph["trace_id"] = parsed_spans[0].trace_id

    # 1. Add all nodes to graph
    for span in parsed_spans:
        node_id = span.span_id
        node_type = map_span_kind_to_node_type(span)
        content = get_span_content(span)

        # Build node metadata incorporating extracted OTel conventions
        metadata = dict(span.attributes)
        tool_name = get_tool_name(span)
        if tool_name:
            metadata["tool_name"] = tool_name
        relevance = get_relevance_score(span)
        if relevance is not None:
            metadata["relevance_score"] = relevance
        if is_span_truncated(span):
            metadata["response_truncated"] = True
        if span.duration_ms > 0:
            metadata["latency_ms"] = span.duration_ms
        if span.status_code == OTelSpanStatus.ERROR:
            metadata["error"] = span.status_message or "span_error"

        g.add_node(
            node_id,
            id=node_id,
            type=node_type.value,
            timestamp=span.start_time,
            content=content,
            metadata=metadata,
            reads_from=[],
            span_kind=span.kind.value,
            parent_span_id=span.parent_span_id,
        )

    # 2. Add edges based on parent_span_id (parent -> child)
    for span in parsed_spans:
        node_id = span.span_id
        if span.parent_span_id and g.has_node(span.parent_span_id):
            g.add_edge(span.parent_span_id, node_id)
            # Record reads_from dependency on child node
            reads_from = g.nodes[node_id].setdefault("reads_from", [])
            if span.parent_span_id not in reads_from:
                reads_from.append(span.parent_span_id)

    return g
