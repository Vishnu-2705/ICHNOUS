"use client";

import React from "react";

interface HeaderProps {
  useMockApi: boolean;
}

export const Header: React.FC<HeaderProps> = ({ useMockApi }) => {
  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-40 px-4 sm:px-6 py-3 flex items-center justify-between shadow-md">
      <div className="flex items-center gap-3">
        <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-red-500 via-amber-500 to-indigo-600 p-[1px] shadow-lg shadow-amber-500/10 shrink-0">
          <div className="h-full w-full bg-slate-950 rounded-[7px] flex items-center justify-center">
            <span className="font-mono text-xs font-bold bg-gradient-to-r from-amber-400 to-red-400 bg-clip-text text-transparent">
              ICH
            </span>
          </div>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-bold text-slate-100 tracking-tight text-base sm:text-lg">
              ICHNOUS
            </h1>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
              Causal Debugger
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono hidden sm:block">
            The Causal Debugger for Autonomous AI Systems
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 font-mono text-xs px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800 shadow-sm">
          <span className="text-slate-400 hidden xs:inline">Mode:</span>
          {useMockApi ? (
            <span className="text-amber-400 font-semibold flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-amber-400 animate-pulse"></span>
              Mock API
            </span>
          ) : (
            <span className="text-emerald-400 font-semibold flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-400"></span>
              Real Backend (8000)
            </span>
          )}
        </div>
      </div>
    </header>
  );
};
