"use client";

import React, { useEffect, useRef, useState } from "react";
import { Header } from "../components/header";
import { TraceSelector } from "../components/trace-selector";
import { ViewMode, ViewToggle } from "../components/view-toggle";
import { LoadingState } from "../components/loading-state";
import { RawTraceView } from "../components/raw-trace-view";
import { TraceGraph } from "../components/trace-graph";
import { DiagnosisCard } from "../components/diagnosis-card";
import { RegressionTestPanel } from "../components/regression-test-panel";
import { LiveAgentDashboard } from "../components/live-agent-dashboard";
import { ErrorState } from "../components/error-state";
import {
  diagnoseTrace,
  generateRegressionTest,
  getTrace,
  getTraces,
} from "../lib/api";
import {
  FullDiagnosisResponse,
  RegressionTest,
  Trace,
  TraceSummary,
} from "../types/tracemind";

export default function HomePage() {
  const useMockApi = process.env.NEXT_PUBLIC_USE_MOCK_API === "true";

  // Application state
  const [traceList, setTraceList] = useState<TraceSummary[]>([]);
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);
  const [selectedTrace, setSelectedTrace] = useState<Trace | null>(null);
  const [diagnosis, setDiagnosis] = useState<FullDiagnosisResponse | null>(null);
  const [regressionTest, setRegressionTest] = useState<RegressionTest | null>(null);
  const [activeView, setActiveView] = useState<ViewMode>("live");
  const [uploadedSessionId, setUploadedSessionId] = useState<string | null>(null);

  // Loading flags
  const [isLoadingTraces, setIsLoadingTraces] = useState<boolean>(true);
  const [isLoadingTrace, setIsLoadingTrace] = useState<boolean>(false);
  const [isDiagnosing, setIsDiagnosing] = useState<boolean>(false);
  const [isGeneratingRegression, setIsGeneratingRegression] = useState<boolean>(false);

  // Error state
  const [error, setError] = useState<string | null>(null);

  const currentRequestIdRef = useRef<string | null>(null);

  // Load static trace list for replay mode
  useEffect(() => {
    let isMounted = true;
    async function loadTraces() {
      setIsLoadingTraces(true);
      setError(null);
      try {
        const summaries = await getTraces();
        if (isMounted) {
          setTraceList(summaries);
          if (summaries.length > 0) {
            setSelectedTraceId(summaries[0].id);
          }
        }
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (isMounted) {
          setIsLoadingTraces(false);
        }
      }
    }

    loadTraces();
    return () => {
      isMounted = false;
    };
  }, []);

  // Selected trace change handler
  const handleSelectTrace = (id: string) => {
    if (id === selectedTraceId) return;
    setSelectedTraceId(id);
    setDiagnosis(null);
    setRegressionTest(null);
    setError(null);
  };

  // Fetch selected trace detail
  useEffect(() => {
    if (!selectedTraceId) return;

    const requestId = selectedTraceId;
    currentRequestIdRef.current = requestId;

    async function fetchTraceDetails() {
      setIsLoadingTrace(true);
      try {
        const trace = await getTrace(requestId);
        if (currentRequestIdRef.current === requestId) {
          setSelectedTrace(trace);
        }
      } catch (err: unknown) {
        if (currentRequestIdRef.current === requestId) {
          setError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (currentRequestIdRef.current === requestId) {
          setIsLoadingTrace(false);
        }
      }
    }

    fetchTraceDetails();
  }, [selectedTraceId]);

  // Diagnose trace action
  const handleDiagnose = async () => {
    if (!selectedTraceId) return;

    const requestId = selectedTraceId;
    setIsDiagnosing(true);
    setError(null);
    try {
      const res = await diagnoseTrace(requestId);
      if (currentRequestIdRef.current === requestId) {
        setDiagnosis(res);
      }
    } catch (err: unknown) {
      if (currentRequestIdRef.current === requestId) {
        setError(err instanceof Error ? err.message : String(err));
      }
    } finally {
      if (currentRequestIdRef.current === requestId) {
        setIsDiagnosing(false);
      }
    }
  };

  // Generate regression test action
  const handleGenerateRegression = async () => {
    if (!selectedTraceId) return;

    setIsGeneratingRegression(true);
    try {
      const test = await generateRegressionTest(selectedTraceId);
      setRegressionTest(test);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsGeneratingRegression(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans antialiased">
      {/* Header */}
      <Header
        useMockApi={useMockApi}
        onUploadComplete={(sessionId) => {
          setUploadedSessionId(sessionId);
          setActiveView("live");
        }}
      />

      {/* Main Workspace Shell */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 flex flex-col gap-6">
        {/* Controls Toolbar */}
        <section className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-sm backdrop-blur-sm">
          {activeView !== "live" ? (
            <TraceSelector
              traces={traceList}
              selectedTraceId={selectedTraceId}
              onSelectTrace={handleSelectTrace}
              disabled={isLoadingTraces || isLoadingTrace}
            />
          ) : (
            <div className="flex items-center gap-2 font-mono text-xs text-slate-300">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="font-bold text-slate-100">Live Agent Runtime Workspace</span>
              <span className="text-slate-500">|</span>
              <span className="text-slate-400">Real-Time Event Stream & Intelligence Engine</span>
            </div>
          )}

          <ViewToggle
            activeView={activeView}
            onViewChange={setActiveView}
            disabled={isLoadingTraces}
          />
        </section>

        {/* Global Error Banner */}
        {error && activeView !== "live" && (
          <section>
            <ErrorState
              title="Execution Error"
              error={error}
              onRetry={() => {
                setError(null);
                if (selectedTraceId) {
                  setSelectedTraceId(selectedTraceId);
                }
              }}
            />
          </section>
        )}

        {/* Main Content Workspace */}
        <section className="flex-1 flex flex-col min-h-[550px] bg-slate-900/40 border border-slate-800/80 rounded-xl p-4 sm:p-6 shadow-md">
          {activeView === "live" ? (
            /* Live Agent Runtime Workspace (Primary) */
            <LiveAgentDashboard uploadedSessionId={uploadedSessionId} />
          ) : activeView === "raw" ? (
            /* Raw JSON View */
            <RawTraceView trace={selectedTrace} isLoading={isLoadingTrace} />
          ) : (
            /* Baseline Static Fixture Replay View */
            <div className="flex flex-col gap-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-3 gap-3">
                <div>
                  <h2 className="text-base font-semibold text-slate-100 tracking-tight">
                    {selectedTrace?.name || "Static Trace Replay"}
                  </h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {selectedTrace?.description || "Select a fixture trace to analyze baseline failure paths"}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={handleDiagnose}
                  disabled={isDiagnosing || !selectedTraceId}
                  className="self-start sm:self-auto px-4 py-2 rounded-lg bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-mono text-xs font-bold shadow-lg shadow-amber-500/10 transition-all flex items-center gap-2 disabled:opacity-50"
                >
                  {isDiagnosing ? (
                    <>
                      <span className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin"></span>
                      Diagnosing Causal Walk...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      Diagnose Causal Path
                    </>
                  )}
                </button>
              </div>

              {isDiagnosing && (
                <LoadingState
                  message="Running backward causal walk..."
                  subtext="Analyzing divergence scores & querying grounded explanation engine"
                />
              )}

              {!isDiagnosing && !diagnosis && (
                <div className="flex flex-col items-center justify-center min-h-[300px] border border-dashed border-slate-800 rounded-lg p-8 text-center bg-slate-950/30">
                  <div className="w-10 h-10 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-400 mb-3">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 01-2 2h-1a2 2 0 01-2-2v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </div>
                  <p className="text-slate-300 font-mono text-sm font-semibold mb-1">
                    Ready to Diagnose Baseline Trace
                  </p>
                  <p className="text-slate-500 font-mono text-xs max-w-md">
                    Click &ldquo;Diagnose Causal Path&rdquo; to analyze root cause, extract evidence nodes, and inspect suggested fixes.
                  </p>
                </div>
              )}

              {!isDiagnosing && diagnosis && (
                <div className="flex flex-col gap-6">
                  {/* Execution Graph Visualization */}
                  <div className="flex flex-col gap-2">
                    <h3 className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider">
                      Reconstructed Causal Execution Graph
                    </h3>
                    <TraceGraph
                      graph={diagnosis.graph}
                      diagnosis={diagnosis.diagnosis}
                      anomalies={diagnosis.anomalies}
                      criticalPath={diagnosis.critical_path}
                    />
                  </div>

                  {/* Diagnosis Results Card */}
                  <DiagnosisCard diagnosis={diagnosis.diagnosis} />

                  {/* Regression Test Artifact Panel */}
                  <RegressionTestPanel
                    regressionTest={regressionTest}
                    traceId={selectedTraceId}
                    onGenerate={handleGenerateRegression}
                    isLoading={isGeneratingRegression}
                  />
                </div>
              )}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
