"use client";

import React from "react";

export type ViewMode = "live" | "ichnous" | "raw";

interface ViewToggleProps {
  activeView: ViewMode;
  onViewChange: (view: ViewMode) => void;
  disabled?: boolean;
}

export const ViewToggle: React.FC<ViewToggleProps> = ({
  activeView,
  onViewChange,
  disabled = false,
}) => {
  return (
    <div className="flex flex-col gap-1.5 w-full sm:w-auto">
      <span className="text-xs font-mono font-medium text-slate-400 uppercase tracking-wider">
        Workspace Perspective
      </span>
      <div className="inline-flex p-1 rounded-lg bg-slate-900 border border-slate-800 self-start shadow-sm flex-wrap gap-1">
        <button
          type="button"
          aria-label="Switch to Live Agent Runtime view"
          onClick={() => onViewChange("live")}
          disabled={disabled}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-mono font-medium transition-all focus:outline-none focus:ring-2 focus:ring-emerald-500/50 ${
            activeView === "live"
              ? "bg-emerald-500/20 text-emerald-300 shadow-sm border border-emerald-500/40 font-bold"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
          }`}
        >
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          ⚡ Live Agent Runtime
        </button>

        <button
          type="button"
          aria-label="Switch to Baseline Fixture Replay view"
          onClick={() => onViewChange("ichnous")}
          disabled={disabled}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-mono font-medium transition-all focus:outline-none focus:ring-2 focus:ring-amber-500/50 ${
            activeView === "ichnous"
              ? "bg-amber-500/20 text-amber-300 shadow-sm border border-amber-500/30 font-semibold"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
          }`}
        >
          <svg className="w-3.5 h-3.5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          📁 Static Fixture Replay
        </button>

        <button
          type="button"
          aria-label="Switch to Raw Trace JSON view"
          onClick={() => onViewChange("raw")}
          disabled={disabled}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-mono font-medium transition-all focus:outline-none focus:ring-2 focus:ring-slate-500/50 ${
            activeView === "raw"
              ? "bg-slate-800 text-slate-100 shadow-sm border border-slate-700/60 font-semibold"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
          }`}
        >
          <svg className="w-3.5 h-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
          </svg>
          Raw Trace JSON
        </button>
      </div>
    </div>
  );
};
