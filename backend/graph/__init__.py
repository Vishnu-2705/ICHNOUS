"""Package initialization for graph module."""

try:
    from graph.analyzer import (
        backward_walk,
        compute_divergence,
        detect_anomalies,
        extract_critical_path,
        find_failure_node,
        rank_root_cause_candidates,
        sort_root_cause_candidates,
        surface_anomalies,
    )
    from graph.builder import (
        build_graph,
        edge_lookup,
        get_graph_statistics,
        get_num_edges,
        get_num_nodes,
        node_lookup,
    )
except ImportError:
    from backend.graph.analyzer import (
        backward_walk,
        compute_divergence,
        detect_anomalies,
        extract_critical_path,
        find_failure_node,
        rank_root_cause_candidates,
        sort_root_cause_candidates,
        surface_anomalies,
    )
    from backend.graph.builder import (
        build_graph,
        edge_lookup,
        get_graph_statistics,
        get_num_edges,
        get_num_nodes,
        node_lookup,
    )

__all__ = [
    "build_graph",
    "get_num_nodes",
    "get_num_edges",
    "node_lookup",
    "edge_lookup",
    "get_graph_statistics",
    "detect_anomalies",
    "surface_anomalies",
    "find_failure_node",
    "extract_critical_path",
    "compute_divergence",
    "backward_walk",
    "sort_root_cause_candidates",
    "rank_root_cause_candidates",
]
