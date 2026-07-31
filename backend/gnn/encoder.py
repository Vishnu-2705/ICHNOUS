"""
Heterogeneous Graph Transformer (HGT) & Multi-Task Neural Network Engine for TraceMind.
Calculates graph attention, heterogeneous node embeddings, vulnerability scores, and multi-task predictions.
"""

import math
from typing import Any, Dict, List, Tuple
import networkx as nx

NODE_TYPE_MAP = {
    "plan": 0,
    "tool_call": 1,
    "observation": 2,
    "reasoning": 3,
    "decision": 4,
    "delegation": 5,
    "final_answer": 6,
}


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-15.0, min(15.0, x))))


def _softmax(vec: List[float]) -> List[float]:
    max_v = max(vec) if vec else 0.0
    exps = [math.exp(v - max_v) for v in vec]
    sum_exps = sum(exps) or 1.0
    return [e / sum_exps for e in exps]


def extract_graph_features(g: nx.DiGraph) -> Tuple[Dict[str, List[float]], Dict[str, float]]:
    """
    Extract multi-dimensional node feature vectors and graph-level topological metrics.
    Node vector (32d):
    - Node type one-hot (7d)
    - Relative execution timestamp (1d)
    - Latency log scale (1d)
    - In-degree & Out-degree (2d)
    - PageRank & Betweenness Centrality (2d)
    - Anomaly / Error indicator (1d)
    - Text semantic hash components (18d)
    """
    node_features: Dict[str, List[float]] = {}

    # Calculate graph centralities
    try:
        pageranks = nx.pagerank(g, alpha=0.85) if len(g) > 1 else {n: 1.0 for n in g}
    except Exception:
        pageranks = {n: 1.0 / max(1, len(g)) for n in g}

    try:
        betweenness = nx.betweenness_centrality(g) if len(g) > 1 else {n: 0.0 for n in g}
    except Exception:
        betweenness = {n: 0.0 for n in g}

    timestamps = [g.nodes[n].get("timestamp", "") for n in g.nodes]
    num_nodes = max(1, len(g.nodes))

    for idx, (nid, data) in enumerate(g.nodes(data=True)):
        ntype = str(data.get("type", "reasoning")).lower()
        type_idx = NODE_TYPE_MAP.get(ntype, 3)
        type_onehot = [1.0 if i == type_idx else 0.0 for i in range(7)]

        rel_time = idx / num_nodes
        latency = float(data.get("metadata", {}).get("latency_ms", 0.0))
        log_latency = math.log1p(max(0.0, latency)) / 10.0

        in_deg = float(g.in_degree(nid)) / max(1.0, float(num_nodes))
        out_deg = float(g.out_degree(nid)) / max(1.0, float(num_nodes))
        pr_score = float(pageranks.get(nid, 0.0))
        bw_score = float(betweenness.get(nid, 0.0))

        metadata = data.get("metadata", {})
        has_error = 1.0 if (
            metadata.get("status") in ("error", "failed", "rate_limit_degraded")
            or metadata.get("response_truncated") is True
            or float(metadata.get("relevance_score", 1.0)) < 0.4
        ) else 0.0

        content = str(data.get("content", ""))
        content_hash = [float((hash(content + str(i)) % 100) / 100.0) for i in range(18)]

        feat_vector = (
            type_onehot
            + [rel_time, log_latency, in_deg, out_deg, pr_score, bw_score, has_error]
            + content_hash
        )
        node_features[nid] = feat_vector

    graph_metrics = {
        "num_nodes": float(len(g.nodes)),
        "num_edges": float(len(g.edges)),
        "density": float(nx.density(g)),
        "is_dag": 1.0 if nx.is_directed_acyclic_graph(g) else 0.0,
    }

    return node_features, graph_metrics


def run_heterogeneous_graph_transformer(
    g: nx.DiGraph,
    node_features: Dict[str, List[float]],
) -> Tuple[Dict[str, float], Dict[str, float], List[float]]:
    """
    Simulates Multi-Head Heterogeneous Graph Attention (HGT) over execution DAG.
    Returns:
    - node_vulnerability_scores: Dict[node_id, score ∈ [0, 1]]
    - edge_attention_weights: Dict["src->dst", weight ∈ [0, 1]]
    - pooled_graph_embedding: List[float] (64d global representation)
    """
    node_vulnerability: Dict[str, float] = {}
    edge_attention: Dict[str, float] = {}

    nodes = list(g.nodes)
    if not nodes:
        return {}, {}, [0.0] * 64

    # Calculate dynamic attention weights for edges
    for u, v in g.edges:
        u_feat = node_features.get(u, [0.0] * 32)
        v_feat = node_features.get(v, [0.0] * 32)

        # Dot-product attention with relation scaling
        dot = sum(a * b for a, b in zip(u_feat[:16], v_feat[:16]))
        attn_val = _sigmoid(dot / 4.0)
        edge_key = f"{u}->{v}"
        edge_attention[edge_key] = round(attn_val, 4)

    # Try to load PyTorch model for inference
    try:
        from gnn.pytorch_model import get_pytorch_model, TORCH_AVAILABLE
    except ImportError:
        try:
            from backend.gnn.pytorch_model import get_pytorch_model, TORCH_AVAILABLE
        except ImportError:
            TORCH_AVAILABLE = False
            
    if TORCH_AVAILABLE:
        model = get_pytorch_model()
        if model is not None:
            import torch
            # Convert node features to tensor
            features_list = [node_features.get(nid, [0.0]*32) for nid in nodes]
            features_tensor = torch.tensor(features_list, dtype=torch.float32)
            
            with torch.no_grad():
                vuln_scores, pooled_emb = model(features_tensor)
                
            # Map back to dict
            for i, nid in enumerate(nodes):
                node_vulnerability[nid] = round(vuln_scores[i].item(), 4)
            pooled_embedding = [round(x, 4) for x in pooled_emb.tolist()]
            
            return node_vulnerability, edge_attention, pooled_embedding

    # --- FALLBACK: Heterogeneous message passing simulation ---
    pooled_vectors: List[List[float]] = []

    for nid in nodes:
        feat = node_features.get(nid, [0.0] * 32)
        in_edges = g.in_edges(nid)
        out_edges = g.out_edges(nid)

        # Aggregate incoming neighbor features weighted by edge attention
        in_attn_sum = 0.0
        for src, _ in in_edges:
            in_attn_sum += edge_attention.get(f"{src}->{nid}", 0.5)

        has_error = feat[13]  # Anomaly flag
        rel_pos = feat[7]     # Relative timestamp

        # Vulnerability equation considering anomaly, attention centrality, and degree
        raw_vulnerability = (
            has_error * 0.55
            + (1.0 if g.nodes[nid].get("type") in ("tool_call", "observation", "delegation") else 0.2) * 0.25
            + (in_attn_sum / max(1.0, float(len(in_edges)))) * 0.20
        )
        vuln_score = min(0.98, max(0.05, _sigmoid((raw_vulnerability - 0.4) * 5.0)))
        node_vulnerability[nid] = round(vuln_score, 4)

        pooled_vectors.append(feat)

    # Global Graph Pooling (Mean + Max pooling)
    graph_dim = 64
    pooled_embedding = [0.0] * graph_dim
    for dim_i in range(min(32, len(pooled_vectors[0]))):
        vals = [vec[dim_i] for vec in pooled_vectors]
        mean_val = sum(vals) / len(vals)
        max_val = max(vals)
        pooled_embedding[dim_i] = round(mean_val, 4)
        pooled_embedding[dim_i + 32] = round(max_val, 4)

    return node_vulnerability, edge_attention, pooled_embedding
