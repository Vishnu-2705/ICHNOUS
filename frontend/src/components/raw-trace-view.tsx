"use client";

import React, { useState } from "react";
import { Trace } from "../types/tracemind";

interface RawTraceViewProps {
  trace: Trace | null;
  isLoading?: boolean;
}

export const RawTraceView: React.FC<RawTraceViewProps> = ({
  trace,
  isLoading = false,
}) => {
  const [copied, setCopied] = useState<boolean>(false);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 min-h-[400px] font-mono text-xs text-slate-400 bg-slate-950 rounded-lg border border-slate-800 animate-pulse">
        Formatting raw JSON payload...
      </div>
    );
  }

  if (!trace) {
    return (
      <div className="flex flex-col items-center justify-center p-12 min-h-[400px] font-mono text-xs text-slate-500 bg-slate-950 rounded-lg border border-slate-800">
        No raw trace data available.
      </div>
    );
  }

  const jsonString = JSON.stringify(trace, null, 2);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(jsonString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback if clipboard API unavailable
      setCopied(false);
    }
  };

  return (
    <div className="flex flex-col gap-3 w-full">
      {/* Header info bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 bg-slate-900/80 px-4 py-2.5 rounded-lg border border-slate-800">
        <div className="flex items-center gap-3 font-mono text-xs">
          <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-semibold">
            JSON Log
          </span>
          <span className="text-slate-200 font-medium">{trace.name}</span>
          <span className="text-slate-500">({trace.nodes.length} execution nodes)</span>
        </div>

        <button
          type="button"
          onClick={handleCopy}
          className="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 font-mono text-xs transition-colors border border-slate-700 flex items-center gap-1.5 self-end sm:self-auto"
        >
          {copied ? (
            <>
              <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-emerald-400 font-semibold">Copied!</span>
            </>
          ) : (
            <>
              <svg className="w-3.5 h-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              Copy JSON
            </>
          )}
        </button>
      </div>

      {/* Code Container */}
      <div className="relative group rounded-lg border border-slate-800 bg-slate-950 overflow-hidden shadow-inner">
        <div className="max-h-[600px] overflow-auto p-4 font-mono text-xs text-slate-300 leading-relaxed scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent">
          <pre className="whitespace-pre-wrap break-words">{jsonString}</pre>
        </div>
      </div>
    </div>
  );
};
