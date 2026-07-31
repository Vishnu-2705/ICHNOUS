"use client";

import React, { useState } from "react";
import { Upload, Sparkles } from "lucide-react";
import { SourceCodeUploadModal } from "./source-code-upload-modal";

interface HeaderProps {
  useMockApi?: boolean;
  onUploadSuccess?: (sessionId: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ useMockApi = false, onUploadSuccess }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      <header className="border-b border-border-strong bg-bg-surface px-4 py-2.5 flex items-center justify-between shadow-sm z-30 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 bg-text-primary text-bg-surface flex items-center justify-center font-display text-xs font-bold shadow-[2px_2px_0px_0px_#171717]">
            ICH
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-display font-bold text-sm tracking-tight text-text-primary uppercase">
                ICHNOUS
              </h1>
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
                Causal Debugger
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setIsModalOpen(true)}
            className="px-3 py-1.5 bg-text-primary text-bg-surface font-display font-bold text-xs uppercase border border-border-strong shadow-[2px_2px_0px_0px_#171717] hover:translate-y-[1px] hover:translate-x-[1px] hover:shadow-none transition-all flex items-center gap-1.5"
          >
            <Upload size={13} />
            <span>Upload Code</span>
          </button>

          <div className="flex items-center gap-2 font-mono text-xs px-2.5 py-1 rounded bg-bg-canvas border border-border-subtle">
            <span className="text-text-secondary hidden xs:inline">Mode:</span>
            {useMockApi ? (
              <span className="text-amber-400 font-semibold flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse"></span>
                Mock API
              </span>
            ) : (
              <span className="text-emerald-400 font-semibold flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
                FastAPI Real Engine
              </span>
            )}
          </div>
        </div>
      </header>

      <SourceCodeUploadModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onUploadSuccess={(sessionId) => {
          if (onUploadSuccess) {
            onUploadSuccess(sessionId);
          }
        }}
      />
    </>
  );
};
