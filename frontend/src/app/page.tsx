"use client";

import React, { useState, useEffect } from "react";
import { ChevronUp, ChevronDown, AlertCircle } from "lucide-react";
import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query";
import { Header } from "../components/header";
import { CasesSidebar } from "../components/sidebar/cases-sidebar";
import { GraphCanvas } from "../components/graph/GraphCanvas";
import { InvestigationSummary } from "../components/summary/InvestigationSummary";
import { InvestigationOverlay } from "../components/overlay/InvestigationOverlay";
import { ExecutionTimeline } from "../components/timeline/ExecutionTimeline";
import { diagnoseTrace, getTrace } from "../lib/api";
import { RevealProvider, useReveal } from "../components/reveal/RevealContext";

function IchnousWorkspaceContent() {
  const [isTimelineOpen, setIsTimelineOpen] = useState(false);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const { phase, startReveal, skipReveal, resetReveal } = useReveal();
  const queryClient = useQueryClient();

  // Fetch the selected case's trace (GraphCanvas uses this via cache too)
  const { data: trace } = useQuery({
    queryKey: ["trace", selectedCaseId],
    queryFn: () => getTrace(selectedCaseId!),
    enabled: !!selectedCaseId,
  });

  // Fetch diagnosis for selected case with 10-minute in-memory caching
  const {
    data: diagnosisData,
    isLoading: isDiagnosing,
    isError: isDiagnoseError,
    refetch: refetchDiagnosis,
  } = useQuery({
    queryKey: ["diagnosis", selectedCaseId],
    queryFn: () => diagnoseTrace(selectedCaseId!),
    enabled: !!selectedCaseId,
    staleTime: 10 * 60 * 1000,
  });

  useEffect(() => {
    if (selectedCaseId) {
      setSelectedNodeId(null);
      resetReveal();
      startReveal();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCaseId]);


  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.shiftKey && e.key.toUpperCase() === "R") {
        e.preventDefault();
        startReveal();
      } else if (e.shiftKey && e.key.toUpperCase() === "S") {
        e.preventDefault();
        skipReveal();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [startReveal, skipReveal]);

  const handleUploadSuccess = (sessionId: string) => {
    queryClient.invalidateQueries({ queryKey: ["cases"] });
    setSelectedCaseId(sessionId);
  };

  return (
    <div className="flex flex-col h-screen w-full bg-bg-base overflow-hidden text-text-primary">
      {/* Top Application Navigation Header */}
      <Header onUploadSuccess={handleUploadSuccess} />

      <div className="lg:hidden flex items-center justify-center flex-1 bg-bg-base text-text-primary p-6 text-center">
        <p className="font-display font-bold text-lg">Ichnous is optimized for desktop.</p>
      </div>

      <div className="hidden lg:grid grid-cols-[280px_1fr_420px] flex-1 w-full bg-bg-base overflow-hidden text-text-primary">
        <CasesSidebar
          selectedCaseId={selectedCaseId}
          onSelectCase={setSelectedCaseId}
        />

        <div className="flex flex-col relative h-full bg-bg-canvas overflow-hidden">
          {selectedCaseId && <InvestigationOverlay />}

          {isDiagnoseError && (
            <div className="absolute inset-0 z-50 flex items-center justify-center pointer-events-none bg-black/10">
              <div className="bg-bg-surface border-[2px] border-border-strong shadow-truth p-6 flex flex-col items-center pointer-events-auto">
                <AlertCircle className="text-color-root-cause mb-3" size={32} />
                <h2 className="font-display font-bold text-lg text-color-root-cause mb-2">Investigation failed.</h2>
                <button
                  onClick={() => refetchDiagnosis()}
                  className="px-4 py-2 border-[2px] border-border-strong shadow-truth hover:translate-y-[2px] hover:translate-x-[2px] hover:shadow-none transition-all font-display font-bold uppercase text-xs"
                >
                  Retry
                </button>
              </div>
            </div>
          )}

          <main className="flex-1 relative overflow-hidden">
            <GraphCanvas
              selectedCaseId={selectedCaseId}
              selectedNodeId={selectedNodeId}
              onSelectNode={setSelectedNodeId}
              diagnosis={diagnosisData || null}
            />
          </main>

          <div
            className={`flex flex-col bg-bg-surface border-t border-border-strong transition-all duration-300 ease-in-out shrink-0 ${
              isTimelineOpen ? "h-36" : "h-11"
            }`}
          >
            <button
              onClick={() => setIsTimelineOpen(!isTimelineOpen)}
              className="flex items-center justify-between px-4 h-11 w-full hover:bg-bg-canvas transition-colors shrink-0 text-xs"
            >
              <div className="flex items-center gap-2">
                <span className="font-display font-bold text-xs uppercase tracking-wider text-text-primary">EXECUTION TIMELINE</span>
                <span className="px-2 py-0.5 rounded-full bg-bg-canvas border border-border-subtle text-[10px] font-mono text-text-secondary">
                  {trace?.nodes?.length || 0} Events
                </span>
              </div>
              <div className="flex items-center gap-1 text-[11px] text-text-secondary font-sans">
                {isTimelineOpen ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
                <span>{isTimelineOpen ? "Collapse" : "Expand"}</span>
              </div>
            </button>

            <ExecutionTimeline trace={trace || null} />
          </div>
        </div>

        <aside className="flex flex-col border-l-[2px] border-border-strong bg-bg-surface z-10 h-full overflow-hidden">
          <InvestigationSummary
            diagnosis={diagnosisData || null}
            trace={trace || null}
            selectedNodeId={selectedNodeId}
            onSelectNode={setSelectedNodeId}
          />

        </aside>
      </div>
    </div>
  );
}

export default function IchnousWorkspace() {
  return (
    <RevealProvider>
      <IchnousWorkspaceContent />
    </RevealProvider>
  );
}
