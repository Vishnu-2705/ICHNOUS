"use client";

import React from "react";

interface LoadingStateProps {
  message?: string;
  subtext?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = "Loading trace data...",
  subtext = "Reconstructing node graph and metadata",
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 min-h-[380px] bg-slate-950/60 rounded-xl border border-slate-800/80 shadow-inner">
      <div className="relative mb-4">
        <div className="w-12 h-12 rounded-full border-2 border-slate-800 border-t-amber-500 animate-spin"></div>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-ping"></div>
        </div>
      </div>
      <p className="text-slate-200 font-mono text-sm font-semibold tracking-wide mb-1">
        {message}
      </p>
      <p className="text-slate-500 font-mono text-xs">
        {subtext}
      </p>
    </div>
  );
};
