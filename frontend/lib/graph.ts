import { Edge, Node } from "@xyflow/react";
import {
  AnomalyFlag,
  DiagnosisResult,
  SerializedGraph,
  SerializedGraphEdge,
  SerializedGraphNode,
} from "../types/tracemind";

export interface CustomNodeData extends Record<string, unknown> {
  id: string;
  type: string;
  label: string;
  content: string;
  timestamp?: string;
  metadata?: Record<string, unknown>;
  visualState: "root_cause" | "evidence" | "critical_path" | "normal";
  anomalies?: AnomalyFlag[];
  severity_score?: number;
  isSelected?: boolean;
}

export function toReactFlowElements(
  graph: SerializedGraph,
  diagnosis?: DiagnosisResult | null,
  anomalies: AnomalyFlag[] = [],
  criticalPath: string[] = []
): { nodes: Node<CustomNodeData>[]; edges: Edge[] } {
  if (!graph || !Array.isArray(graph.nodes)) {
    return { nodes: [], edges: [] };
  }

  const rootCauseId = diagnosis?.root_cause_node_id || "";
  const evidenceIdsSet = new Set(diagnosis?.evidence_node_ids || []);
  const criticalPathSet = new Set(criticalPath || []);

  const anomalyMap = new Map<string, AnomalyFlag[]>();
  for (const a of anomalies) {
    if (!anomalyMap.has(a.node_id)) {
      anomalyMap.set(a.node_id, []);
    }
    anomalyMap.get(a.node_id)!.push(a);
  }

  // Calculate top-to-bottom or left-to-right deterministic layout coordinates
  const nodeCount = graph.nodes.length;
  const nodesPerRow = Math.min(4, Math.max(2, Math.ceil(Math.sqrt(nodeCount))));
  const horizontalSpacing = 280;
  const verticalSpacing = 160;

  const nodes: Node<CustomNodeData>[] = graph.nodes.map((n: SerializedGraphNode, index: number) => {
    // Derive visual state priority: root_cause > evidence > critical_path > normal
    let visualState: "root_cause" | "evidence" | "critical_path" | "normal" = "normal";

    if (n.id === rootCauseId || n.highlight === "root_cause" || n.is_root_cause) {
      visualState = "root_cause";
    } else if (evidenceIdsSet.has(n.id) || n.highlight === "evidence" || n.is_evidence) {
      visualState = "evidence";
    } else if (criticalPathSet.has(n.id) || n.highlight === "critical_path" || n.is_critical_path) {
      visualState = "critical_path";
    }

    const row = Math.floor(index / nodesPerRow);
    const col = index % nodesPerRow;
    const x = col * horizontalSpacing;
    const y = row * verticalSpacing;

    const nodeAnomalies = anomalyMap.get(n.id) || [];

    return {
      id: n.id,
      type: "customNode",
      position: { x, y },
      data: {
        id: n.id,
        type: n.type || "unknown",
        label: n.label || n.content || n.id,
        content: n.content || n.label || "",
        timestamp: n.timestamp,
        metadata: n.metadata,
        visualState,
        anomalies: nodeAnomalies,
        severity_score: n.severity_score,
      },
    };
  });

  const rawEdges: SerializedGraphEdge[] = Array.isArray(graph.edges) ? graph.edges : [];
  const edges: Edge[] = rawEdges.map((e: SerializedGraphEdge, idx: number) => {
    const source = e.source || e.from || "";
    const target = e.target || e.to || "";
    const edgeId = e.id || `edge-${source}-${target}-${idx}`;

    const isEvidenceEdge =
      e.highlight === "evidence" ||
      e.is_evidence ||
      (evidenceIdsSet.has(source) && evidenceIdsSet.has(target));

    const isCriticalEdge =
      e.highlight === "critical_path" ||
      e.is_critical_path ||
      (criticalPathSet.has(source) && criticalPathSet.has(target));

    let strokeColor = "#475569"; // slate-600 default
    let strokeWidth = 1.5;
    let animated = false;

    if (isEvidenceEdge) {
      strokeColor = "#f59e0b"; // amber-500
      strokeWidth = 2.5;
      animated = true;
    } else if (isCriticalEdge) {
      strokeColor = "#818cf8"; // indigo-400
      strokeWidth = 2;
    }

    return {
      id: edgeId,
      source,
      target,
      animated,
      style: {
        stroke: strokeColor,
        strokeWidth,
      },
    };
  });

  return { nodes, edges };
}
