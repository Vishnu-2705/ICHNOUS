"use client";

import React, { useState } from "react";
import { SDKIntegrationModal } from "./sdk-integration-modal";
import { SourceCodeUploadModal } from "./source-code-upload-modal";

interface HeaderProps {
  useMockApi: boolean;
  onUploadComplete?: (sessionId: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ useMockApi, onUploadComplete }) => {
  const [isSdkModalOpen, setIsSdkModalOpen] = useState<boolean>(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState<boolean>(false);

  return (
    <>
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-40 px-4 sm:px-6 py-3 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-amber-500 via-emerald-500 to-indigo-600 p-[1px] shadow-lg shadow-amber-500/10 shrink-0">
            <div className="h-full w-full bg-slate-950 rounded-[7px] flex items-center justify-center">
              <span className="font-mono text-xs font-bold bg-gradient-to-r from-amber-400 to-emerald-400 bg-clip-text text-transparent">
                TM
              </span>
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-slate-100 tracking-tight text-base sm:text-lg">
                TraceMind
              </h1>
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
                Live Agent OS v0.2.0
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono hidden sm:block">
              The Causal Debugger & Real-Time Observability for Autonomous AI Systems
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setIsUploadModalOpen(true)}
            className="px-3 py-1.5 rounded-md bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-300 font-mono text-xs font-semibold transition-all flex items-center gap-1.5 shadow-sm"
          >
            <svg className="w-3.5 h-3.5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            <span>Upload Agent Code</span>
          </button>

          <button
            type="button"
            onClick={() => setIsSdkModalOpen(true)}
            className="px-3 py-1.5 rounded-md bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-mono text-xs font-semibold transition-all flex items-center gap-1.5 shadow-sm"
          >
            <svg className="w-3.5 h-3.5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
            </svg>
            <span className="hidden sm:inline">SDK Integration Guide</span>
          </button>

          <div className="flex items-center gap-2 font-mono text-xs px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800 shadow-sm">
            <span className="text-slate-400 hidden xs:inline">Engine:</span>
            {useMockApi ? (
              <span className="text-amber-400 font-semibold flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-amber-400 animate-pulse"></span>
                Mock
              </span>
            ) : (
              <span className="text-emerald-400 font-semibold flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
                Backend Live (8000)
              </span>
            )}
          </div>
        </div>
      </header>

      <SDKIntegrationModal isOpen={isSdkModalOpen} onClose={() => setIsSdkModalOpen(false)} />
      <SourceCodeUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onAnalysisComplete={(sessionId) => {
          if (onUploadComplete) onUploadComplete(sessionId);
        }}
      />
    </>
  );
};
