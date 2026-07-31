"""
GNN Regression Intelligence Engine Service for TraceMind.
Orchestrates graph feature extraction, HGT encoder inference, multi-task heads, memory bank indexing, and GNNExplainer.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
import networkx as nx

try:
    from gnn.encoder import extract_graph_features, run_heterogeneous_graph_transformer
    from gnn.explainer import explain_gnn_prediction
    from gnn.heads import evaluate_multi_task_heads
    from gnn.memory_bank import get_memory_bank
    from models.trace import (
        DiagnosisResult,
        GNNPredictionResponse,
        NodeVulnerability,
        SuggestedFix,
        Trace,
    )
except ImportError:
    from backend.gnn.encoder import extract_graph_features, run_heterogeneous_graph_transformer
    from backend.gnn.explainer import explain_gnn_prediction
    from backend.gnn.heads import evaluate_multi_task_heads
    from backend.gnn.memory_bank import get_memory_bank
    from backend.models.trace import (
        DiagnosisResult,
        GNNPredictionResponse,
        NodeVulnerability,
        SuggestedFix,
        Trace,
    )


def run_gnn_regression_intelligence(
    trace: Trace,
    g: nx.DiGraph,
    diagnosis: Optional[DiagnosisResult] = None,
) -> GNNPredictionResponse:
    """
    Executes the full GNN Regression Intelligence Engine pipeline:
    Graph Feature Extraction -> Heterogeneous Graph Transformer -> Multi-Task Prediction -> GNNExplainer -> Vector Memory Bank Indexing.
    """
    t_start = time.perf_counter()

    # 1. Graph Feature Extraction
    node_features, graph_metrics = extract_graph_features(g)

    # 2. Heterogeneous Graph Transformer (HGT) Inference
    node_vuln, edge_attn, pooled_vec = run_heterogeneous_graph_transformer(g, node_features)

    # 3. Multi-Task Prediction Heads Evaluation
    prediction_head_out = evaluate_multi_task_heads(g, node_vuln, pooled_vec)

    # 4. GNNExplainer Minimal Subgraph Extraction
    expl_nodes, expl_edges = explain_gnn_prediction(
        g,
        node_vuln,
        edge_attn,
        prediction_head_out.predicted_root_cause_node_id,
    )

    # 5. Graph Memory Bank Vector Search & Indexing
    memory_bank = get_memory_bank()
    similar_matches = memory_bank.search_similar_motifs(pooled_vec, top_k=2)
    similar_trace_ids = [match[0] for match in similar_matches]
    memory_bank.add_graph_vector(trace.id, pooled_vec)

    # 6. Formulate NodeVulnerability list for response
    vulnerable_nodes_list = []
    for nid, score in node_vuln.items():
        vulnerable_nodes_list.append(
            NodeVulnerability(
                node_id=nid,
                vulnerability_score=score,
                attention_weight=edge_attn.get(f"{nid}->{nid}", 0.5),
                is_root_cause_candidate=(nid == prediction_head_out.predicted_root_cause_node_id),
            )
        )
    vulnerable_nodes_list.sort(key=lambda x: x.vulnerability_score, reverse=True)

    # 7. Formulate Suggested Fix based on prediction
    if diagnosis and diagnosis.suggested_fix:
        suggested_fix = diagnosis.suggested_fix
        explanation = f"[GNN Intelligence Engine] {diagnosis.explanation}"
    else:
        fix_type = (
            "prompt_patch"
            if prediction_head_out.failure_category == "Retrieval"
            else "tool_schema_fix"
            if prediction_head_out.failure_category == "Tool"
            else "guardrail_addition"
        )
        suggested_fix = SuggestedFix(
            type=fix_type,
            target=f"node_{prediction_head_out.predicted_root_cause_node_id}_boundary",
            diff=f"+ Protect against {prediction_head_out.failure_category} anomaly at node '{prediction_head_out.predicted_root_cause_node_id}'",
        )
        explanation = (
            f"[GNN Intelligence Engine] Predicted {prediction_head_out.failure_category} anomaly "
            f"at root-cause node '{prediction_head_out.predicted_root_cause_node_id}' with "
            f"{prediction_head_out.confidence_score*100:.1f}% confidence."
        )

    t_end = time.perf_counter()
    execution_time_ms = round((t_end - t_start) * 1000.0, 2)

    return GNNPredictionResponse(
        trace_id=trace.id,
        engine_version="v2.4-HeteroGraphTransformer",
        regression_probability=prediction_head_out.regression_probability,
        failure_probability=prediction_head_out.failure_probability,
        failure_category=prediction_head_out.failure_category,
        failure_severity=prediction_head_out.failure_severity,
        confidence_score=prediction_head_out.confidence_score,
        predicted_root_cause_node_id=prediction_head_out.predicted_root_cause_node_id,
        vulnerable_nodes=vulnerable_nodes_list,
        explanation_subgraph_nodes=expl_nodes,
        explanation_subgraph_edges=expl_edges,
        similar_historical_traces=similar_trace_ids,
        explanation=explanation,
        suggested_fix=suggested_fix,
        execution_time_ms=execution_time_ms,
    )
