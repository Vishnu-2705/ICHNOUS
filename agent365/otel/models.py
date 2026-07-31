"""
OpenTelemetry GenAI & OpenInference Transport Models for Agent 365.

Provides Pydantic models and helper extractors for:
- OpenTelemetry GenAI semantic conventions (gen_ai.*)
- OpenInference span specifications (openinference.span.kind)
- W3C Trace Context (trace_id, span_id, parent_span_id)
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class OpenInferenceSpanKind(str, Enum):
    """OpenInference span classification kinds."""

    LLM = "LLM"
    CHAIN = "CHAIN"
    TOOL = "TOOL"
    AGENT = "AGENT"
    RETRIEVER = "RETRIEVER"
    RAG = "RAG"
    UNKNOWN = "UNKNOWN"


class OTelSpanStatus(str, Enum):
    """Standard OpenTelemetry span status codes."""

    UNSET = "UNSET"
    OK = "OK"
    ERROR = "ERROR"


class OTelSpan(BaseModel):
    """
    Representation of an OpenTelemetry GenAI / OpenInference span.
    """

    span_id: str
    parent_span_id: Optional[str] = None
    trace_id: str
    name: str
    kind: OpenInferenceSpanKind = OpenInferenceSpanKind.UNKNOWN
    start_time: str = ""
    end_time: str = ""
    duration_ms: float = 0.0
    status_code: OTelSpanStatus = OTelSpanStatus.UNSET
    status_message: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    events: List[Dict[str, Any]] = Field(default_factory=list)

    @classmethod
    def from_otlp_dict(cls, data: Dict[str, Any]) -> "OTelSpan":
        """
        Construct an OTelSpan from standard OTLP JSON dictionary format.
        """
        attributes = data.get("attributes", {})
        if isinstance(attributes, list):
            # OTLP KeyValue list format
            attr_dict = {}
            for item in attributes:
                key = item.get("key")
                val_obj = item.get("value", {})
                val = (
                    val_obj.get("stringValue")
                    or val_obj.get("intValue")
                    or val_obj.get("doubleValue")
                    or val_obj.get("boolValue")
                    or val_obj
                )
                if key:
                    attr_dict[key] = val
            attributes = attr_dict

        # Detect OpenInference span kind from attributes or name
        raw_kind = attributes.get("openinference.span.kind") or attributes.get("span.kind")
        kind = OpenInferenceSpanKind.UNKNOWN
        if raw_kind:
            try:
                kind = OpenInferenceSpanKind(str(raw_kind).upper())
            except ValueError:
                kind = OpenInferenceSpanKind.UNKNOWN

        # Status code parsing
        raw_status = data.get("status", {})
        status_code = OTelSpanStatus.UNSET
        if isinstance(raw_status, dict):
            code_str = str(raw_status.get("code", "UNSET")).upper()
            if "ERROR" in code_str or code_str == "2":
                status_code = OTelSpanStatus.ERROR
            elif "OK" in code_str or code_str == "1":
                status_code = OTelSpanStatus.OK
        status_msg = raw_status.get("message") if isinstance(raw_status, dict) else None

        duration = data.get("duration_ms", 0.0)
        if not duration and data.get("start_time") and data.get("end_time"):
            # Compute latency if ISO timestamps available
            pass

        return cls(
            span_id=str(data.get("span_id", data.get("spanId", ""))),
            parent_span_id=str(data.get("parent_span_id", data.get("parentSpanId", ""))) or None,
            trace_id=str(data.get("trace_id", data.get("traceId", ""))),
            name=str(data.get("name", "span")),
            kind=kind,
            start_time=str(data.get("start_time", "")),
            end_time=str(data.get("end_time", "")),
            duration_ms=float(duration),
            status_code=status_code,
            status_message=status_msg,
            attributes=attributes,
            events=data.get("events", []),
        )


# ---------------------------------------------------------------------------
# Attribute Extractor Helpers
# ---------------------------------------------------------------------------
def get_span_content(span: OTelSpan) -> str:
    """Extract human-readable content or prompt/completion from span attributes."""
    attrs = span.attributes
    # OTel GenAI conventions
    if "gen_ai.prompt" in attrs:
        return str(attrs["gen_ai.prompt"])
    if "gen_ai.completion" in attrs:
        return str(attrs["gen_ai.completion"])

    # OpenInference conventions
    if "input.value" in attrs:
        return str(attrs["input.value"])
    if "output.value" in attrs:
        return str(attrs["output.value"])

    # Fallback to span name
    return span.name


def get_tool_name(span: OTelSpan) -> Optional[str]:
    """Extract tool name if this span represents a tool invocation."""
    attrs = span.attributes
    return (
        attrs.get("tool.name")
        or attrs.get("gen_ai.tool.name")
        or attrs.get("tool_name")
    )


def get_relevance_score(span: OTelSpan) -> Optional[float]:
    """Extract retrieval relevance score if present."""
    attrs = span.attributes
    val = (
        attrs.get("retrieval.relevance_score")
        or attrs.get("relevance_score")
        or attrs.get("score")
    )
    if val is not None:
        try:
            return float(val)
        except (ValueError, TypeError):
            pass
    return None


def is_span_truncated(span: OTelSpan) -> bool:
    """Check if tool/LLM response was truncated."""
    attrs = span.attributes
    return bool(
        attrs.get("response_truncated")
        or attrs.get("gen_ai.truncated")
        or attrs.get("truncated")
    )
