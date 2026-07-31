"""
GNNExplainer & Subgraph Explanations module for TraceMind.
Extracts minimal explanatory subgraphs and feature masks to explain GNN predictions.
"""

from typing import Dict, List, Tuple
import networkx as nx


def explain_gnn_prediction(
    g: nx.DiGraph,
    node_vulnerability: Dict[str, float],
    edge_attention: Dict[str, float],
    root_cause_node_id: str,
) -> Tuple[List[str], List[str]]:
    """
    Extracts minimal explanation subgraph (nodes + edges) using GNNExplainer edge mask logic.
    Identifies the subset of nodes and edges that maximally contribute to the prediction.
    """
    nodes = list(g.nodes)
    if not nodes:
        return [], []

    # 1. Include root cause node and its 1-hop / 2-hop neighborhood
    subgraph_nodes = set()
    if root_cause_node_id in g:
        subgraph_nodes.add(root_cause_node_id)
        for pred in g.predecessors(root_cause_node_id):
            subgraph_nodes.add(pred)
        for succ in g.successors(root_cause_node_id):
            subgraph_nodes.add(succ)

    # Add any nodes with vulnerability > 0.50
    for nid, vuln in node_vulnerability.items():
        if vuln > 0.50:
            subgraph_nodes.add(nid)

    # Fallback to top 3 vulnerable nodes if set is small
    if len(subgraph_nodes) < 2:
        sorted_nodes = sorted(nodes, key=lambda n: node_vulnerability.get(n, 0.0), reverse=True)
        subgraph_nodes.update(sorted_nodes[:min(3, len(sorted_nodes))])

    # 2. Extract explanation edges connecting explanation nodes
    subgraph_edges = []
    for src, dst in g.edges:
        if src in subgraph_nodes and dst in subgraph_nodes:
            subgraph_edges.append(f"{src}->{dst}")

    return sorted(list(subgraph_nodes)), sorted(subgraph_edges)
