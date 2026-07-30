"""
Graph Builder module for TraceMind.

Constructs networkx.DiGraph from Trace models and provides graph statistics and lookup functions.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import networkx as nx

try:
    from models.trace import Trace
except ImportError:
    from backend.models.trace import Trace


def build_graph(trace: Trace) -> nx.DiGraph:
    """
    Convert a Trace into a directed graph (networkx.DiGraph).

    Every TraceNode becomes one graph node with all metadata stored.
    Every reads_from relation becomes a directed edge (upstream -> downstream).
    """
    g = nx.DiGraph(trace_id=trace.id, trace_name=trace.name)

    node_ids = {n.id for n in trace.nodes}

    for node in trace.nodes:
        node_type = node.type.value if hasattr(node.type, "value") else str(node.type)
        g.add_node(
            node.id,
            id=node.id,
            type=node_type,
            timestamp=node.timestamp,
            content=node.content,
            metadata=node.metadata,
            reads_from=node.reads_from,
        )

    for node in trace.nodes:
        for upstream_id in node.reads_from:
            if upstream_id in node_ids:
                g.add_edge(upstream_id, node.id)

    return g


def get_num_nodes(g: nx.DiGraph) -> int:
    """Return the total number of nodes in the graph."""
    return g.number_of_nodes()


def get_num_edges(g: nx.DiGraph) -> int:
    """Return the total number of edges in the graph."""
    return g.number_of_edges()


def node_lookup(g: nx.DiGraph, node_id: str) -> Optional[Dict[str, Any]]:
    """
    Look up a node by its ID.

    Returns a dict of node attributes if present, or None if node does not exist.
    """
    if g.has_node(node_id):
        return dict(g.nodes[node_id])
    return None


def edge_lookup(g: nx.DiGraph, source_id: str, target_id: str) -> Optional[Dict[str, Any]]:
    """
    Look up a directed edge from source_id to target_id.

    Returns edge attribute dict if the directed edge exists, or None if not present.
    """
    if g.has_edge(source_id, target_id):
        return dict(g.edges[source_id, target_id])
    return None


def get_graph_statistics(g: nx.DiGraph) -> Dict[str, Any]:
    """
    Return graph statistics including node count and edge count.
    """
    return {
        "num_nodes": get_num_nodes(g),
        "num_edges": get_num_edges(g),
        "is_dag": nx.is_directed_acyclic_graph(g),
    }
