"use client";

import React, { useCallback, useMemo, useState } from "react";
import {
  Background,
  Controls,
  Node,
  ReactFlow,
  useEdgesState,
  useNodesState,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { AnomalyFlag, DiagnosisResult, SerializedGraph } from "../types/tracemind";
import { CustomGraphNode } from "./graph-node";
import { CustomNodeData, toReactFlowElements } from "../lib/graph";

interface TraceGraphProps {
  graph: SerializedGraph;
  diagnosis?: DiagnosisResult | null;
  anomalies?: AnomalyFlag[];
  criticalPath?: string[];
}

export const TraceGraph: React.FC<TraceGraphProps> = ({
  graph,
  diagnosis,
  anomalies = [],
  criticalPath = [],
}) => {
  const [selectedNodeData, setSelectedNodeData] = useState<CustomNodeData | null>(null);

  // Convert serialized graph to React Flow elements
  const { nodes: initialNodes, edges: initialEdges } = useMemo(
    () => toReactFlowElements(graph, diagnosis, anomalies, criticalPath),
    [graph, diagnosis, anomalies, criticalPath]
  );

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  const nodeTypes = useMemo(() => ({ customNode: CustomGraphNode }), []);

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNodeData(node.data as unknown as CustomNodeData);
  }, []);

  const closeDetails = useCallback(() => {
    setSelectedNodeData(null);
  }, []);

  if (!graph || !graph.nodes || graph.nodes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] border border-slate-800 rounded-xl bg-slate-950/60 p-8 text-slate-500 font-mono text-xs">
        No graph nodes found in serialized payload.
      </div>
    );
  }

  return (
    <div className="relative w-full h-[540px] rounded-xl border border-slate-800 bg-slate-950 overflow-hidden shadow-2xl">
      {/* Legend Header */}
      <div className="absolute top-3 left-3 z-10 flex flex-wrap items-center gap-3 px-3.5 py-2 rounded-lg bg-slate-900/90 border border-slate-800 backdrop-blur-md font-mono text-[11px]">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shadow shadow-rose-500/50"></span>
          <span className="text-slate-200 font-semibold">Root Cause</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
          <span className="text-slate-300">Evidence Node/Path</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-indigo-400"></span>
          <span className="text-slate-300">Critical Path</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-slate-600"></span>
          <span className="text-slate-400">Normal Node</span>
        </div>
      </div>

      {/* React Flow Canvas */}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.2}
        maxZoom={1.5}
        className="bg-slate-950"
      >
        <Background color="#334155" gap={20} size={1} />
        <Controls className="!bg-slate-900 !border-slate-800 !text-slate-200" />
      </ReactFlow>

      {/* Node Details Drawer/Modal */}
      {selectedNodeData && (
        <div className="absolute top-3 right-3 z-20 w-80 max-h-[500px] overflow-y-auto rounded-xl bg-slate-900/95 border border-slate-700/80 p-4 shadow-2xl backdrop-blur-md text-xs font-mono text-slate-200">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
            <div className="flex items-center gap-2">
              <span className="font-bold text-amber-400">#{selectedNodeData.id}</span>
              <span className="uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[10px]">
                {selectedNodeData.type}
              </span>
            </div>
            <button
              type="button"
              onClick={closeDetails}
              className="text-slate-400 hover:text-slate-100 p-1"
            >
              ✕
            </button>
          </div>

          <div className="flex flex-col gap-3">
            <div>
              <span className="text-slate-400 uppercase text-[10px] block mb-1">Content</span>
              <p className="bg-slate-950 p-2.5 rounded border border-slate-800 leading-relaxed text-slate-200 whitespace-pre-wrap">
                {selectedNodeData.content}
              </p>
            </div>

            {selectedNodeData.timestamp && (
              <div>
                <span className="text-slate-400 uppercase text-[10px] block">Timestamp</span>
                <span className="text-slate-300">{selectedNodeData.timestamp}</span>
              </div>
            )}

            {selectedNodeData.metadata && Object.keys(selectedNodeData.metadata).length > 0 && (
              <div>
                <span className="text-slate-400 uppercase text-[10px] block mb-1">Metadata</span>
                <pre className="bg-slate-950 p-2 rounded border border-slate-800 text-[10px] text-slate-300 overflow-x-auto">
                  {JSON.stringify(selectedNodeData.metadata, null, 2)}
                </pre>
              </div>
            )}

            {selectedNodeData.anomalies && selectedNodeData.anomalies.length > 0 && (
              <div>
                <span className="text-rose-400 font-bold uppercase text-[10px] block mb-1">
                  Anomalies Detected
                </span>
                <div className="flex flex-col gap-1">
                  {selectedNodeData.anomalies.map((a, i) => (
                    <div key={i} className="bg-rose-950/30 border border-rose-900/50 p-2 rounded text-rose-300 text-[10px]">
                      <span className="font-bold uppercase">{a.anomaly_type}</span> (Severity: {a.severity_score})
                      <p className="mt-0.5 text-slate-300">{a.details}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
