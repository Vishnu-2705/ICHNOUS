"""
Session-to-Trace Converter for TraceMind.

Converts live TraceSession objects and TraceEvent streams into Pydantic Trace
models compatible with the existing diagnosis pipeline.
"""

from __future__ import annotations

from typing import Dict, List, Optional
import networkx as nx

try:
    from models.session import (
        EVENT_TYPE_TO_NODE_TYPE,
        EventType,
        TraceEvent,
        TraceSession,
        map_event_type_to_node_type,
    )
    from models.trace import NodeType, Trace, TraceNode
except ImportError:
    from backend.models.session import (
        EVENT_TYPE_TO_NODE_TYPE,
        EventType,
        TraceEvent,
        TraceSession,
        map_event_type_to_node_type,
    )
    from backend.models.trace import NodeType, Trace, TraceNode


def event_to_trace_node(event: TraceEvent) -> TraceNode:
    """
    Convert a single TraceEvent into a TraceNode suitable for graph construction.
    """
    node_id = event.event_id
    node_type = map_event_type_to_node_type(event.event_type)

    # Preserve event metadata while injecting runtime attributes
    metadata = dict(event.metadata) if event.metadata else {}
    metadata["event_type"] = event.event_type.value
    if event.agent_id:
        metadata["agent_id"] = event.agent_id
    if event.parent_event_id:
        metadata["parent_event_id"] = event.parent_event_id
    if event.sequence_number is not None:
        metadata["sequence_number"] = event.sequence_number

    return TraceNode(
        id=node_id,
        type=node_type,
        timestamp=event.timestamp,
        content=event.content,
        metadata=metadata,
        reads_from=event.reads_from or [],
    )


def session_to_trace(session: TraceSession) -> Trace:
    """
    Convert a live TraceSession into a full Pydantic Trace object.
    
    Used for seamlessly plugging live session execution graphs into the existing
    anomaly detection, backward walk, and diagnosis algorithms.
    """
    trace_nodes = [event_to_trace_node(evt) for evt in session.events]

    return Trace(
        id=session.session_id,
        name=session.name,
        description=session.description,
        nodes=trace_nodes,
        expected_failure_category="",
    )
