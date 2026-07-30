"use client";

import React, { memo } from "react";
import { Handle, NodeProps, Position } from "@xyflow/react";
import { CustomNodeData } from "../lib/graph";

const nodeTypeColors: Record<string, { bg: string; text: string; border: string }> = {
  plan: { bg: "bg-blue-500/10", text: "text-blue-400", border: "border-blue-500/30" },
  tool_call: { bg: "bg-amber-500/10", text: "text-amber-400", border: "border-amber-500/30" },
  observation: { bg: "bg-emerald-500/10", text: "text-emerald-400", border: "border-emerald-500/30" },
  reasoning: { bg: "bg-purple-500/10", text: "text-purple-400", border: "border-purple-500/30" },
  decision: { bg: "bg-cyan-500/10", text: "text-cyan-400", border: "border-cyan-500/30" },
  delegation: { bg: "bg-orange-500/10", text: "text-orange-400", border: "border-orange-500/30" },
  final_answer: { bg: "bg-pink-500/10", text: "text-pink-400", border: "border-pink-500/30" },
};

export const CustomGraphNode = memo(({ data }: NodeProps) => {
  const nodeData = data as unknown as CustomNodeData;
  const { id, type, content, visualState, anomalies = [] } = nodeData;

  const typeStyle = nodeTypeColors[type] || {
    bg: "bg-slate-800/40",
    text: "text-slate-300",
    border: "border-slate-700/50",
  };

  let containerStyles = "border-slate-800 bg-slate-900/80 text-slate-300 opacity-85 hover:opacity-100 hover:border-slate-700";
  let badge = null;

  if (visualState === "root_cause") {
    containerStyles =
      "border-2 border-rose-500 bg-slate-950 text-slate-100 shadow-xl shadow-rose-500/20 ring-2 ring-rose-500/30 animate-pulse";
    badge = (
      <span className="px-2 py-0.5 text-[10px] font-mono font-bold uppercase rounded bg-rose-500 text-slate-950 tracking-wider shadow">
        ROOT CAUSE
      </span>
    );
  } else if (visualState === "evidence") {
    containerStyles =
      "border-2 border-amber-500 bg-slate-900/90 text-slate-100 shadow-lg shadow-amber-500/10 ring-1 ring-amber-500/30";
    badge = (
      <span className="px-2 py-0.5 text-[10px] font-mono font-bold uppercase rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
        EVIDENCE
      </span>
    );
  } else if (visualState === "critical_path") {
    containerStyles =
      "border border-indigo-500/70 bg-slate-900/80 text-slate-200 shadow-md shadow-indigo-500/5";
    badge = (
      <span className="px-1.5 py-0.5 text-[9px] font-mono font-semibold uppercase rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">
        CRITICAL PATH
      </span>
    );
  }

  const truncatedContent =
    content.length > 90 ? `${content.slice(0, 90)}...` : content;

  return (
    <div className={`w-64 rounded-xl p-3 backdrop-blur-md transition-all ${containerStyles}`}>
      <Handle type="target" position={Position.Top} className="!bg-slate-500 !w-2 !h-2" />

      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-1.5 overflow-hidden">
          <span className="font-mono text-xs font-bold text-slate-400">#{id}</span>
          <span
            className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded border uppercase ${typeStyle.bg} ${typeStyle.text} ${typeStyle.border}`}
          >
            {type}
          </span>
        </div>
        {badge}
      </div>

      <p className="text-xs font-mono line-clamp-3 leading-relaxed text-slate-300 mb-1">
        {truncatedContent}
      </p>

      {anomalies.length > 0 && (
        <div className="mt-2 pt-1.5 border-t border-slate-800/80 flex items-center gap-1 text-[10px] font-mono text-rose-400">
          <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-ping"></span>
          <span>{anomalies.length} anomaly detected</span>
        </div>
      )}

      <Handle type="source" position={Position.Bottom} className="!bg-slate-500 !w-2 !h-2" />
    </div>
  );
});

CustomGraphNode.displayName = "CustomGraphNode";
