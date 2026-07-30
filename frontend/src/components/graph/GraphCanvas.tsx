import React, { useMemo, useEffect, useState } from "react";
import { ReactFlow, Background, useReactFlow, ReactFlowProvider, NodeChange, applyNodeChanges, Node } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useQuery } from "@tanstack/react-query";
import { getTrace } from "../../lib/api";
import { mapTraceToReactFlow } from "../../lib/graphMapper";
import { GraphEmptyState } from "./GraphEmptyState";
import { GraphNode } from "./GraphNode";
import { GraphEdge } from "./GraphEdge";
import { Loader2, Maximize2, Lock, ZoomIn, Hand, MousePointer, Plus, Minus } from "lucide-react";
import { useReveal } from "../reveal/RevealContext";
import { FullDiagnosisResponse } from "../../types/tracemind";

interface GraphCanvasProps {
  selectedCaseId: string | null;
  selectedNodeId: string | null;
  onSelectNode: (id: string | null) => void;
  diagnosis: FullDiagnosisResponse | null;
}

function GraphRenderer({ selectedCaseId, selectedNodeId, onSelectNode, diagnosis }: GraphCanvasProps) {
  const { phase } = useReveal();
  const { fitView, zoomIn, zoomOut } = useReactFlow();

  const { data: trace, isLoading } = useQuery({
    queryKey: ["trace", selectedCaseId],
    queryFn: () => getTrace(selectedCaseId!),
    enabled: !!selectedCaseId,
  });

  const nodeTypes = useMemo(() => ({ customNode: GraphNode }), []);
  const edgeTypes = useMemo(() => ({ customEdge: GraphEdge }), []);

  const { nodes: initialNodes, edges } = useMemo(() => {
    if (!trace) return { nodes: [], edges: [] };
    return mapTraceToReactFlow(trace, diagnosis);
  }, [trace, diagnosis]);

  // Local state for draggable node positions
  const [nodes, setNodes] = useState<Node[]>([]);

  // Sync nodes with initial layout when trace or diagnosis changes, or when reveal resets
  useEffect(() => {
    setNodes(initialNodes);
  }, [initialNodes]);

  // Replay resets node positions back to default Dagre positions
  useEffect(() => {
    if (phase === "pending" || phase === "overlay") {
      setNodes(initialNodes);
    }
  }, [phase, initialNodes]);

  // Handle node position changes live during dragging
  const handleNodesChange = (changes: NodeChange[]) => {
    setNodes((nds) => applyNodeChanges(changes, nds));
  };

  // Inject isSelected state and onSelectNode into custom nodes
  const nodesWithSelection = useMemo(() => {
    return nodes.map((node) => ({
      ...node,
      data: {
        ...node.data,
        isSelected: node.id === selectedNodeId,
        onSelectNode: (id: string) => {
          onSelectNode(id === selectedNodeId ? null : id);
        },
      },
    }));
  }, [nodes, selectedNodeId, onSelectNode]);

  // Escape key deselects node
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onSelectNode(null);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onSelectNode]);

  // Camera pan when phase hits 'camera'
  useEffect(() => {
    if (phase === "camera") {
      fitView({ padding: 0.2, duration: 1500 });
    }
  }, [phase, fitView]);

  if (!selectedCaseId) {
    return (
      <div className="w-full h-full relative">
        <GraphEmptyState />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-bg-canvas text-text-primary">
        <div className="flex flex-col items-center">
          <Loader2 className="animate-spin mb-2" size={24} />
          <p className="text-text-secondary text-sm">Loading trace data...</p>
        </div>
      </div>
    );
  }

  const isInteractive = phase === "complete";

  return (
    <div className="w-full h-full relative flex flex-col">
      {/* Top Header Bar inside Canvas matching reference image */}
      <div className="h-12 px-4 border-b border-border-strong bg-bg-surface flex items-center justify-between z-30 shrink-0">
        <div className="flex items-center gap-2.5">
          <span className="font-display font-bold text-sm text-text-primary">
            {trace?.name || "Pricing API Failure"}
          </span>
          <span className="px-2 py-0.5 rounded-full border border-border-subtle text-[11px] font-sans text-text-secondary bg-bg-canvas">
            {trace?.description || "Checkout Service"}
          </span>
        </div>

        {/* Top Right Controls matching reference image */}
        <div className="flex items-center gap-1.5 font-sans text-xs">
          <button
            onClick={() => fitView({ duration: 300 })}
            className="px-2.5 py-1 border border-border-subtle bg-bg-surface text-text-primary hover:bg-bg-canvas transition-colors rounded text-xs"
          >
            Fit
          </button>
          <button
            className="px-2.5 py-1 border border-border-subtle bg-bg-surface text-text-primary hover:bg-bg-canvas transition-colors rounded text-xs font-mono"
          >
            100%
          </button>
          <button onClick={() => zoomIn()} className="p-1.5 border border-border-subtle bg-bg-surface text-text-secondary hover:text-text-primary hover:bg-bg-canvas transition-colors rounded">
            <ZoomIn size={14} />
          </button>
          <button className="p-1.5 border border-border-subtle bg-bg-surface text-text-secondary hover:text-text-primary hover:bg-bg-canvas transition-colors rounded">
            <Lock size={14} />
          </button>
          <button onClick={() => fitView({ duration: 300 })} className="p-1.5 border border-border-subtle bg-bg-surface text-text-secondary hover:text-text-primary hover:bg-bg-canvas transition-colors rounded">
            <Maximize2 size={14} />
          </button>
        </div>
      </div>

      {/* Canvas Area */}
      <div className="flex-1 relative overflow-hidden">
        {/* Hero Title Floating Card in Top Left */}
        <div className="absolute top-6 left-6 z-20 pointer-events-auto bg-bg-surface p-5 border-2 border-border-strong shadow-[4px_4px_0px_0px_#171717] w-[320px]">
          <div className="text-[10px] font-display font-bold uppercase tracking-widest text-text-secondary mb-1">
            CUSTOMER SUPPORT AGENT
          </div>
          <h1 className="font-display font-bold text-xl uppercase tracking-wide text-text-primary leading-tight">
            {(trace?.name || "PRICING API FAILURE") + " INVESTIGATION"}
          </h1>
        </div>

        {/* Bottom Left Square Controls matching reference image */}
        <div className="absolute bottom-6 left-6 z-20 flex items-center gap-1.5 bg-bg-surface p-1.5 border-2 border-border-strong shadow-[2px_2px_0px_0px_#171717]">
          <button className="p-1.5 border border-border-strong bg-bg-canvas text-text-primary hover:translate-y-[1px] transition-all">
            <Hand size={14} />
          </button>
          <button className="p-1.5 border border-border-subtle bg-bg-surface text-text-secondary hover:text-text-primary hover:bg-bg-canvas transition-colors">
            <MousePointer size={14} />
          </button>
          <button onClick={() => zoomIn()} className="p-1.5 border border-border-subtle bg-bg-surface text-text-secondary hover:text-text-primary hover:bg-bg-canvas transition-colors">
            <Plus size={14} />
          </button>
          <button onClick={() => zoomOut()} className="p-1.5 border border-border-subtle bg-bg-surface text-text-secondary hover:text-text-primary hover:bg-bg-canvas transition-colors">
            <Minus size={14} />
          </button>
          <button onClick={() => fitView({ duration: 300 })} className="p-1.5 border border-border-subtle bg-bg-surface text-text-secondary hover:text-text-primary hover:bg-bg-canvas transition-colors">
            <Maximize2 size={14} />
          </button>
        </div>

        <ReactFlow
          nodes={nodesWithSelection}
          edges={edges}
          onNodesChange={handleNodesChange}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          onPaneClick={() => onSelectNode(null)}
          fitView
          panOnDrag={isInteractive}
          zoomOnScroll={isInteractive}
          zoomOnPinch={isInteractive}
          panOnScroll={false}
          nodesDraggable={isInteractive}
          zoomOnDoubleClick={false}
          nodesConnectable={false}
          proOptions={{ hideAttribution: true }}
          minZoom={0.1}
          maxZoom={1.5}
          className={isInteractive ? "bg-bg-canvas cursor-grab active:cursor-grabbing" : "bg-bg-canvas cursor-default"}
        >
          <Background color="#CBD5E1" gap={24} size={1.5} />
        </ReactFlow>
      </div>
    </div>
  );
}

export function GraphCanvas(props: GraphCanvasProps) {
  return (
    <ReactFlowProvider>
      <GraphRenderer {...props} />
    </ReactFlowProvider>
  );
}
