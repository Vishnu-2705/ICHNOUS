"use client";

import React from "react";
import { TraceSummary } from "../types/tracemind";

interface TraceSelectorProps {
  traces: TraceSummary[];
  selectedTraceId: string | null;
  onSelectTrace: (id: string) => void;
  disabled?: boolean;
}

export const TraceSelector: React.FC<TraceSelectorProps> = ({
  traces,
  selectedTraceId,
  onSelectTrace,
  disabled = false,
}) => {
  return (
    <div className="flex flex-col gap-1.5 w-full sm:w-auto">
      <label
        htmlFor="trace-select-dropdown"
        className="text-xs font-mono font-medium text-slate-400 uppercase tracking-wider"
      >
        Select Recorded Trace
      </label>
      <div className="relative">
        <select
          id="trace-select-dropdown"
          aria-label="Select Recorded Trace"
          value={selectedTraceId || ""}
          onChange={(e) => onSelectTrace(e.target.value)}
          disabled={disabled || traces.length === 0}
          className="w-full sm:w-80 bg-slate-900 border border-slate-700/80 hover:border-slate-600 focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500 rounded-lg px-3.5 py-2 text-sm text-slate-100 font-medium shadow-sm transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed appearance-none"
        >
          {traces.length === 0 ? (
            <option value="">No traces available</option>
          ) : (
            traces.map((t) => (
              <option key={t.id} value={t.id} className="bg-slate-900 text-slate-100 py-1">
                {t.name}
              </option>
            ))
          )}
        </select>
        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-400">
          <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20">
            <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
          </svg>
        </div>
      </div>
    </div>
  );
};
