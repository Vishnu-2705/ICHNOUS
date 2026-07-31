import React from "react";
import { Trace } from "../../types/tracemind";
import { AlertTriangle, Search, Wrench, BrainCircuit, Key, Mail, CheckCircle2 } from "lucide-react";
import { useReveal } from "../reveal/RevealContext";
import clsx from "clsx";

const getTimelineIcon = (type: string, isRoot?: boolean) => {
  if (isRoot) return <AlertTriangle size={14} className="text-[#EF4444]" />;
  switch (type) {
    case "plan": return <Key size={14} className="text-[#9333EA]" />;
    case "retrieval":
    case "delegation": return <Search size={14} className="text-[#0284C7]" />;
    case "tool_call":
    case "tool": return <Wrench size={14} className="text-[#16A34A]" />;
    case "reasoning":
    case "observation": return <BrainCircuit size={14} className="text-[#6B7280]" />;
    case "response": return <Mail size={14} className="text-[#6B7280]" />;
    default: return <CheckCircle2 size={14} className="text-text-secondary" />;
  }
};

const formatShortAction = (item: { id: string; type: string; title?: string; content?: string }) => {
  const customTitle = (item as { title?: string }).title;
  if (customTitle && customTitle !== item.type) return customTitle;

  if (item.id === "planning_01" || item.type === "plan") return "Create plan";
  if (item.id === "retrieval_01") return "Search docs";
  if (item.id === "retrieval_02") return "Fetch data";
  if (item.id === "tool_01") return "Get profile";
  if (item.id === "tool_02") return "Calc discount";
  if (item.id === "reasoning_01") return "Validate rules";
  if (item.id === "decision_01") return "Return price";
  if (item.id === "response_01") return "Format response";
  if (item.id === "response_02") return "Send to user";

  const raw = item.content || "";
  if (raw.includes("policy")) return "Search docs";
  if (raw.includes("discount")) return "Calc discount";
  if (raw.includes("rules")) return "Validate rules";

  return item.type.replace(/_/g, ' ');
};

export function ExecutionTimeline({ trace }: { trace: Trace | null }) {
  const { phase } = useReveal();
  
  if (!trace) {
    return (
      <div className="flex-1 flex justify-center items-center p-4">
        <p className="text-text-secondary text-xs font-sans">No execution loaded.</p>
      </div>
    );
  }

  const showTimeline = phase === "complete" || phase === "timeline";

  const timelineItems = trace.nodes && trace.nodes.length > 0 ? trace.nodes : [
    { id: "planning_01", type: "plan", title: "Create plan", timestamp: "10:24:10 AM" },
    { id: "retrieval_01", type: "retrieval", title: "Search docs", timestamp: "10:24:12 AM" },
    { id: "retrieval_02", type: "retrieval", title: "Fetch data", timestamp: "10:24:13 AM" },
    { id: "tool_01", type: "tool", title: "Get profile", timestamp: "10:24:14 AM" },
    { id: "tool_02", type: "tool", title: "Calc discount", timestamp: "10:24:15 AM" },
    { id: "reasoning_01", type: "reasoning", title: "Validate rules", timestamp: "10:24:16 AM" },
    { id: "decision_01", type: "decision", title: "Return price", timestamp: "10:24:17 AM", isRoot: true },
    { id: "response_01", type: "response", title: "Format response", timestamp: "10:24:18 AM" },
    { id: "response_02", type: "response", title: "Send to user", timestamp: "10:24:19 AM" },
  ];

  return (
    <div className="flex-1 overflow-x-auto no-scrollbar relative flex items-center px-4 py-2">
      {showTimeline ? (
        <div className="relative flex items-center min-w-full">
          {/* Continuous backbone line running directly through icon centers */}
          <div className="absolute top-[16px] left-[60px] right-[60px] h-[1px] bg-border-subtle z-0" />

          {/* Fixed equal-width event columns */}
          <div className="flex items-start z-10">
            {timelineItems.map((item, idx) => {
              const isRoot = item.type === "root_cause" || item.id === "decision_01" || Boolean((item as { isRoot?: boolean }).isRoot);
              const formattedTime = item.timestamp 
                ? (item.timestamp.includes("T") ? new Date(item.timestamp).toLocaleTimeString() : item.timestamp) 
                : "10:24:10 AM";
              const actionLabel = formatShortAction(item);

              return (
                <div
                  key={item.id}
                  className="w-[120px] shrink-0 flex flex-col items-center text-center px-1"
                >
                  {/* Status Icon sitting directly on backbone line */}
                  <div
                    className={clsx(
                      "w-8 h-8 rounded-full border flex items-center justify-center z-10 transition-all bg-bg-surface",
                      isRoot
                        ? "border-[#EF4444] bg-[#FEF2F2] ring-2 ring-red-100"
                        : "border-border-subtle"
                    )}
                  >
                    {getTimelineIcon(item.type, isRoot)}
                  </div>

                  {/* Timestamp (10px muted) */}
                  <span className="font-mono text-[10px] text-text-secondary opacity-75 mt-2">
                    {formattedTime}
                  </span>

                  {/* Node Name (12px medium weight) */}
                  <span className={clsx(
                    "font-sans text-[12px] font-medium line-clamp-1 mt-0.5",
                    isRoot ? "text-[#EF4444]" : "text-text-primary"
                  )}>
                    {item.id}
                  </span>

                  {/* Short Description (11px muted, concise action) */}
                  <span className="font-sans text-[11px] text-text-secondary line-clamp-2 mt-0.5 leading-tight">
                    {actionLabel}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="w-full flex justify-center py-4">
          <p className="text-text-secondary text-xs font-sans">Synchronizing timeline with root cause...</p>
        </div>
      )}
    </div>
  );
}
