import React from "react";
import { Handle, Position } from "@xyflow/react";
import { BrainCircuit, Wrench, Search, ListTodo, CheckCircle2, AlertTriangle } from "lucide-react";
import clsx from "clsx";
import { useReveal } from "../reveal/RevealContext";

export interface GraphNodeData {
  id: string;
  type: string;
  title: string;
  content?: string;
  timestamp?: string;
  state: "idle" | "analyzing" | "evidence" | "root_cause" | "focused" | "dimmed";
  isRootCause?: boolean;
  isEvidence?: boolean;
  isSelected?: boolean;
  onSelectNode?: (id: string) => void;
}

const getNodeIcon = (type: string) => {
  switch (type) {
    case "plan": return <ListTodo size={13} className="shrink-0" />;
    case "tool_call":
    case "tool": return <Wrench size={13} className="shrink-0" />;
    case "observation": return <Search size={13} className="shrink-0" />;
    case "reasoning": return <BrainCircuit size={13} className="shrink-0" />;
    case "decision": return <AlertTriangle size={13} className="shrink-0" />;
    case "retrieval":
    case "delegation": return <Search size={13} className="shrink-0" />;
    default: return <Search size={13} className="shrink-0" />;
  }
};

const getCategoryStyles = (type: string, isRootCause?: boolean, isEvidence?: boolean, isSelected?: boolean) => {
  if (isRootCause) {
    return {
      bg: "bg-[#FEF2F2]",
      border: "border-2 border-[#EF4444]",
      text: "text-[#EF4444]",
      shadow: isSelected ? "shadow-[4px_4px_0px_0px_rgba(239,68,68,0.3)] ring-2 ring-[#EF4444] ring-offset-1" : "shadow-[4px_4px_0px_0px_rgba(239,68,68,0.2)]"
    };
  }
  if (isEvidence) {
    return {
      bg: "bg-[#FFFBEB]",
      border: "border-[1.5px] border-[#F59E0B]",
      text: "text-[#F59E0B]",
      shadow: isSelected ? "ring-2 ring-[#F59E0B] ring-offset-1 shadow-md" : "shadow-none"
    };
  }
  switch (type) {
    case "plan":
      return {
        bg: "bg-[#FAF5FF]",
        border: "border border-[#E9D5FF]",
        text: "text-[#9333EA]",
        shadow: isSelected ? "ring-2 ring-[#9333EA] ring-offset-1 shadow-md" : "shadow-none"
      };
    case "retrieval":
    case "delegation":
      return {
        bg: "bg-[#F0F9FF]",
        border: "border border-[#BAE6FD]",
        text: "text-[#0284C7]",
        shadow: isSelected ? "ring-2 ring-[#0284C7] ring-offset-1 shadow-md" : "shadow-none"
      };
    case "tool_call":
    case "tool":
      return {
        bg: "bg-[#F0FDF4]",
        border: "border border-[#BBF7D0]",
        text: "text-[#16A34A]",
        shadow: isSelected ? "ring-2 ring-[#16A34A] ring-offset-1 shadow-md" : "shadow-none"
      };
    case "reasoning":
    case "observation":
    case "decision":
    default:
      return {
        bg: "bg-[#F9FAFB]",
        border: "border border-[#E5E7EB]",
        text: "text-[#6B7280]",
        shadow: isSelected ? "ring-2 ring-text-primary ring-offset-1 shadow-md" : "shadow-none"
      };
  }
};

const PHASE_ORDER = ["pending", "overlay", "dim", "evidence", "edges", "camera", "root_cause", "summary", "timeline", "complete"];

export function GraphNode({ data }: { data: GraphNodeData }) {
  const { phase } = useReveal();
  const currentPhaseIdx = PHASE_ORDER.indexOf(phase);
  
  let visualState = data.state;
  if (currentPhaseIdx >= PHASE_ORDER.indexOf("dim")) {
     if (data.isRootCause && currentPhaseIdx >= PHASE_ORDER.indexOf("root_cause")) {
       visualState = "root_cause";
     } else if ((data.isEvidence || data.isRootCause) && currentPhaseIdx >= PHASE_ORDER.indexOf("evidence")) {
       visualState = "evidence";
     } else {
       visualState = "dimmed";
     }
  }

  const isRoot = visualState === "root_cause" || data.isRootCause;
  const isEvid = visualState === "evidence" || data.isEvidence;
  const isSelected = Boolean(data.isSelected);
  const styles = getCategoryStyles(data.type, isRoot, isEvid, isSelected);

  const handleSelect = (e: React.SyntheticEvent) => {
    e.stopPropagation();
    data.onSelectNode?.(data.id);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleSelect(e);
    }
  };

  return (
    <div
      tabIndex={0}
      role="button"
      aria-selected={isSelected}
      onClick={handleSelect}
      onKeyDown={handleKeyDown}
      className={clsx(
        "w-[230px] p-3 rounded-lg font-sans flex flex-col justify-between cursor-grab active:cursor-grabbing outline-none transition-all duration-150 ease-out",
        styles.bg,
        styles.border,
        styles.shadow,
        isSelected ? "z-30 border-text-primary" : "relative",
        visualState === "dimmed" && !isSelected && "opacity-30 grayscale-[0.3]"
      )}
    >
      <Handle type="target" position={Position.Top} className="!w-0 !h-0 !border-0 opacity-0" />
      
      {/* Top Row: Icon + Node Type + Status */}
      <div className="flex items-center justify-between mb-1.5 shrink-0">
        <div className="flex items-center gap-1.5">
          <div className={clsx(styles.text)}>
            {getNodeIcon(data.type)}
          </div>
          <span className="font-display font-thin text-[11px] uppercase tracking-wider text-text-secondary">
            {data.title || data.type.replace(/_/g, ' ')}
          </span>
        </div>
        <div className="flex items-center gap-1">
          {isRoot ? (
            <AlertTriangle size={12} className="text-[#EF4444] animate-pulse" />
          ) : isEvid ? (
            <CheckCircle2 size={12} className="text-[#F59E0B]" />
          ) : (
            <CheckCircle2 size={12} className="text-text-secondary opacity-40" />
          )}
        </div>
      </div>

      {/* Second Row: Primary Content */}
      <div className="text-[13px] font-medium text-text-primary leading-snug line-clamp-2 mb-2">
        {data.content || data.title}
      </div>

      {/* Third Row: Metadata */}
      <div className="flex justify-between items-center text-[10px] text-text-secondary pt-1 border-t border-black/5 font-mono shrink-0">
        <span className="truncate max-w-[100px]" title={data.id}>
          {data.id}
        </span>
        <span className="opacity-70">
          {data.timestamp ? (data.timestamp.includes("T") ? new Date(data.timestamp).toLocaleTimeString() : data.timestamp) : "10:24:12 AM"}
        </span>
      </div>

      <Handle type="source" position={Position.Bottom} className="!w-0 !h-0 !border-0 opacity-0" />
    </div>
  );
}
