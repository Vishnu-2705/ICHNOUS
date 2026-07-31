import { Trace, FullDiagnosisResponse } from "../types/tracemind";
import { Node, Edge } from "@xyflow/react";
import dagre from "dagre";

const NODE_WIDTH = 230;
const NODE_HEIGHT = 120;

export function mapTraceToReactFlow(trace: Trace, diagnosis: FullDiagnosisResponse | null): { nodes: Node[]; edges: Edge[] } {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: "TB", nodesep: 80, ranksep: 100 });

  const nodes: Node[] = [];
  const edges: Edge[] = [];

  const rootCauseId = diagnosis?.diagnosis?.root_cause_node_id;
  const evidenceIds = new Set(diagnosis?.diagnosis?.evidence_node_ids || []);
  const criticalPath = new Set(diagnosis?.critical_path || []);

  trace.nodes.forEach((traceNode) => {
    dagreGraph.setNode(traceNode.id, { width: NODE_WIDTH, height: NODE_HEIGHT });

    traceNode.reads_from?.forEach((sourceId) => {
      const edgeId = `e-${sourceId}-${traceNode.id}`;
      // An edge is on the evidence path if both source and target are in the critical path
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
    const nodeWithPosition = dagreGraph.node(traceNode.id);
    const titleMap: Record<string, string> = {
      plan: "Planning",
      tool_call: "Tool Call",
      observation: "Observation",
      reasoning: "Reasoning",
      decision: "Decision",
      delegation: "Retrieval",
      final_answer: "Final Answer",
    };
    
    nodes.push({
      id: traceNode.id,
      type: "customNode",
      position: { x: nodeWithPosition.x - NODE_WIDTH / 2, y: nodeWithPosition.y - NODE_HEIGHT / 2 },
      data: {
        id: traceNode.id,
        type: traceNode.type,
        title: titleMap[traceNode.type] || traceNode.type,
        content: (traceNode as { content?: string; description?: string }).content || (traceNode as { description?: string }).description || "",
        timestamp: traceNode.timestamp,
        state: "idle",
        isRootCause: traceNode.id === rootCauseId,
        isEvidence: evidenceIds.has(traceNode.id),
      },
    });
  });

  return { nodes, edges };
}
