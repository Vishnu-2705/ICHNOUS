"use client";

import React, { useState } from "react";
import { SuggestedFix as SuggestedFixModel } from "../types/tracemind";

interface SuggestedFixProps {
  fix: SuggestedFixModel;
}

const fixTypeBadges: Record<string, { label: string; bg: string; text: string; border: string }> = {
  prompt_patch: {
    label: "PROMPT PATCH",
    bg: "bg-blue-500/10",
    text: "text-blue-400",
    border: "border-blue-500/30",
  },
  tool_schema_fix: {
    label: "TOOL SCHEMA FIX",
    bg: "bg-purple-500/10",
    text: "text-purple-400",
    border: "border-purple-500/30",
  },
  retry_policy: {
    label: "RETRY POLICY",
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    border: "border-amber-500/30",
  },
  guardrail_addition: {
    label: "GUARDRAIL ADDITION",
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
    border: "border-emerald-500/30",
  },
};

export const SuggestedFix: React.FC<SuggestedFixProps> = ({ fix }) => {
  const [copied, setCopied] = useState<boolean>(false);

  const badgeStyle = fixTypeBadges[fix.type] || {
    label: fix.type.toUpperCase().replace(/_/g, " "),
    bg: "bg-slate-800/40",
    text: "text-slate-300",
    border: "border-slate-700/50",
  };

  const handleCopyDiff = async () => {
    try {
      await navigator.clipboard.writeText(fix.diff);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  const diffLines = fix.diff.split("\n");

  return (
    <div className="flex flex-col gap-3 bg-slate-950 p-4 rounded-xl border border-slate-800 shadow-inner">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2.5">
          <span className={`px-2.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${badgeStyle.bg} ${badgeStyle.text} ${badgeStyle.border}`}>
            {badgeStyle.label}
          </span>
          <span className="text-xs font-mono text-slate-300 font-medium truncate max-w-md">
            Target: <code className="text-amber-300 font-semibold">{fix.target}</code>
          </span>
        </div>

        <button
          type="button"
          onClick={handleCopyDiff}
          className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 font-mono text-[11px] transition-colors border border-slate-700 flex items-center gap-1.5 self-end sm:self-auto"
        >
          {copied ? (
            <span className="text-emerald-400 font-semibold flex items-center gap-1">
              ✓ Copied Diff
            </span>
          ) : (
            <span>Copy Diff</span>
          )}
        </button>
      </div>

      {/* Code Diff Renderer */}
      <div className="bg-slate-900/90 rounded-lg border border-slate-800/90 p-3 overflow-x-auto font-mono text-xs leading-relaxed">
        {diffLines.map((line, idx) => {
          let lineStyle = "text-slate-400";
          if (line.startsWith("+") && !line.startsWith("+++")) {
            lineStyle = "text-emerald-400 bg-emerald-950/30 px-1 rounded-sm";
          } else if (line.startsWith("-") && !line.startsWith("---")) {
            lineStyle = "text-rose-400 bg-rose-950/30 px-1 rounded-sm";
          } else if (line.startsWith("@@") || line.startsWith("---") || line.startsWith("+++")) {
            lineStyle = "text-amber-400 font-bold opacity-90";
          }

          return (
            <div key={idx} className={`whitespace-pre ${lineStyle}`}>
              {line}
            </div>
          );
        })}
      </div>
    </div>
  );
};
