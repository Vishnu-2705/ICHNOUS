import { Trace, FullDiagnosisResponse, SerializedGraphNode, SerializedGraphEdge } from "../types/tracemind";
import { Node, Edge } from "@xyflow/react";
import dagre from "dagre";

const NODE_WIDTH = 230;
const NODE_HEIGHT = 120;

export function mapTraceToReactFlow(
  trace: Trace | null,
  diagnosis: FullDiagnosisResponse | null
): { nodes: Node[]; edges: Edge[] } {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: "TB", nodesep: 80, ranksep: 100 });

  const nodes: Node[] = [];
  const edges: Edge[] = [];

  const rootCauseId = diagnosis?.diagnosis?.root_cause_node_id;
  const evidenceIds = new Set(diagnosis?.diagnosis?.evidence_node_ids || []);
  const criticalPath = new Set(diagnosis?.critical_path || []);

  // Title map for node types
  const titleMap: Record<string, string> = {
    plan: "Planning",
    tool_call: "Tool Call",
    observation: "Observation",
    reasoning: "Reasoning",
    decision: "Decision",
    delegation: "Retrieval",
    final_answer: "Final Answer",
  };

  // Case A: Use diagnosis.graph if populated from FastAPI backend
  if (diagnosis?.graph && Array.isArray(diagnosis.graph.nodes) && diagnosis.graph.nodes.length > 0) {
    const serializedNodes: SerializedGraphNode[] = diagnosis.graph.nodes;
    const serializedEdges: SerializedGraphEdge[] = diagnosis.graph.edges || [];

    serializedNodes.forEach((sNode) => {
      dagreGraph.setNode(sNode.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
    });

    serializedEdges.forEach((sEdge) => {
      const source = sEdge.source || sEdge.from || "";
      const target = sEdge.target || sEdge.to || "";
      if (source && target) {
        const edgeId = `e-${source}-${target}`;
        const isEvidencePath =
          sEdge.is_evidence ||
          sEdge.highlight === "evidence" ||
          (criticalPath.has(source) && criticalPath.has(target));

        edges.push({
          id: edgeId,
          source,
          target,
          type: "customEdge",
          data: { isEvidencePath },
          animated: false,
        });
        dagreGraph.setEdge(source, target);
      }
    });

    dagre.layout(dagreGraph);

    serializedNodes.forEach((sNode) => {
      const pos = dagreGraph.node(sNode.id) || { x: 100, y: 100 };
      const isRoot = sNode.is_root_cause || sNode.id === rootCauseId;
      const isEvid = sNode.is_evidence || evidenceIds.has(sNode.id);

      nodes.push({
        id: sNode.id,
        type: "customNode",
        position: { x: pos.x - NODE_WIDTH / 2, y: pos.y - NODE_HEIGHT / 2 },
        data: {
          id: sNode.id,
          type: sNode.type,
          title: titleMap[sNode.type] || sNode.type,
          content: sNode.content || "",
          timestamp: sNode.timestamp || "",
          state: "idle",
          isRootCause: isRoot,
          isEvidence: isEvid,
        },
      });
    });

    return { nodes, edges };
  }

  // Case B: Fallback to trace.nodes if diagnosis.graph not yet available
  if (!trace || !Array.isArray(trace.nodes) || trace.nodes.length === 0) {
    return { nodes: [], edges: [] };
  }

  trace.nodes.forEach((traceNode) => {
    dagreGraph.setNode(traceNode.id, { width: NODE_WIDTH, height: NODE_HEIGHT });

    traceNode.reads_from?.forEach((sourceId) => {
      const edgeId = `e-${sourceId}-${traceNode.id}`;
      const isEvidencePath = criticalPath.has(sourceId) && criticalPath.has(traceNode.id);

      edges.push({
        id: edgeId,
        source: sourceId,
        target: traceNode.id,
        type: "customEdge",
        data: { isEvidencePath },
        animated: false,
      });
      dagreGraph.setEdge(sourceId, traceNode.id);
    });
  });

  dagre.layout(dagreGraph);

  trace.nodes.forEach((traceNode) => {
    const nodeWithPosition = dagreGraph.node(traceNode.id) || { x: 100, y: 100 };

    nodes.push({
      id: traceNode.id,
      type: "customNode",
      position: { x: nodeWithPosition.x - NODE_WIDTH / 2, y: nodeWithPosition.y - NODE_HEIGHT / 2 },
      data: {
        id: traceNode.id,
        type: traceNode.type,
        title: titleMap[traceNode.type] || traceNode.type,
        content:
          (traceNode as { content?: string; description?: string }).content ||
          (traceNode as { description?: string }).description ||
          "",
        timestamp: traceNode.timestamp,
        state: "idle",
        isRootCause: traceNode.id === rootCauseId,
        isEvidence: evidenceIds.has(traceNode.id),
      },
    });
  });

  return { nodes, edges };
}

