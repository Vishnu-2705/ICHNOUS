"use client";

import React, { useEffect, useState } from "react";
import { diagnoseSession, getSessions, triggerLiveDemo } from "../lib/api";
import { useTraceMindWebSocket } from "../lib/websocket";
import { FullDiagnosisResponse, SessionSummary, TraceEvent } from "../types/tracemind";
import { DiagnosisCard } from "./diagnosis-card";
import { LoadingState } from "./loading-state";
import { TraceGraph } from "./trace-graph";

interface LiveAgentDashboardProps {
  uploadedSessionId?: string | null;
}

export const LiveAgentDashboard: React.FC<LiveAgentDashboardProps> = ({ uploadedSessionId }) => {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(uploadedSessionId || null);
  const [isLoadingSessions, setIsLoadingSessions] = useState<boolean>(true);
  const [isTriggeringDemo, setIsTriggeringDemo] = useState<boolean>(false);
  const [selectedScenario, setSelectedScenario] = useState<string>("retrieval_failure");
  const [manualDiagnosis, setManualDiagnosis] = useState<FullDiagnosisResponse | null>(null);
  const [isDiagnosingManual, setIsDiagnosingManual] = useState<boolean>(false);

  // Auto-select newly uploaded session when prop updates
  useEffect(() => {
    if (uploadedSessionId) {
      setSelectedSessionId(uploadedSessionId);
      loadSessionList(uploadedSessionId);
      // Auto-diagnose uploaded session
      diagnoseSession(uploadedSessionId)
        .then((res) => setManualDiagnosis(res))
        .catch((err) => console.error("Error auto-diagnosing uploaded session:", err));
    }
  }, [uploadedSessionId]);

  // Connect real-time WebSocket hook
  const { isConnected, graph, diagnosis: wsDiagnosis, requestSnapshot } = useTraceMindWebSocket(selectedSessionId);

  // Combine WS diagnosis and manual diagnosis
  const activeDiagnosis = wsDiagnosis || manualDiagnosis;

  // 1. Initial sessions load
  const loadSessionList = async (targetId?: string | null) => {
    try {
      const res = await getSessions();
      setSessions(res.items);
      const activeId = targetId || selectedSessionId;
      if (res.items.length > 0 && !activeId) {
        setSelectedSessionId(res.items[0].session_id);
      }
    } catch (err) {
      console.error("Error loading live sessions:", err);
    } finally {
      setIsLoadingSessions(false);
    }
  };

  useEffect(() => {
    loadSessionList();
  }, []);

  // 2. Trigger live agent simulation
  const handleRunDemo = async () => {
    setIsTriggeringDemo(true);
    setManualDiagnosis(null);
    try {
      await triggerLiveDemo(selectedScenario);
      // Wait briefly then refresh sessions
      setTimeout(async () => {
        const res = await getSessions();
        setSessions(res.items);
        if (res.items.length > 0) {
          setSelectedSessionId(res.items[0].session_id);
        }
        setIsTriggeringDemo(false);
      }, 800);
    } catch (err) {
      console.error("Error triggering live demo:", err);
      setIsTriggeringDemo(false);
    }
  };

  // 3. Trigger manual mid-session diagnosis
  const handleDiagnoseOnDemand = async () => {
    if (!selectedSessionId) return;
    setIsDiagnosingManual(true);
    try {
      const res = await diagnoseSession(selectedSessionId);
      setManualDiagnosis(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      console.warn("Diagnosis call error:", msg);
      if (msg.includes("404")) {
        // Session expired or backend restarted - refresh sessions and pick latest
        const res = await getSessions();
        setSessions(res.items);
        if (res.items.length > 0) {
          setSelectedSessionId(res.items[0].session_id);
          try {
            const freshRes = await diagnoseSession(res.items[0].session_id);
            setManualDiagnosis(freshRes);
          } catch {
            setManualDiagnosis(null);
          }
        } else {
          setSelectedSessionId(null);
          setManualDiagnosis(null);
        }
      }
    } finally {
      setIsDiagnosingManual(false);
    }
  };

  const currentSession = sessions.find((s) => s.session_id === selectedSessionId);

  return (
    <div className="flex flex-col gap-6 w-full">
      {/* Controls & Action Bar */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 shadow-lg backdrop-blur-md">
        {/* Left: Session Selector */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 w-full lg:w-auto">
          <div className="flex flex-col gap-1 w-full sm:w-auto">
            <label className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
              Live Agent Session
            </label>
            <select
              value={selectedSessionId || ""}
              onChange={(e) => {
                setSelectedSessionId(e.target.value);
                setManualDiagnosis(null);
              }}
              disabled={isLoadingSessions || sessions.length === 0}
              className="bg-slate-950 border border-slate-700/80 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:ring-2 focus:ring-amber-500/50 min-w-[280px]"
            >
              {sessions.length === 0 ? (
                <option value="">No live sessions found</option>
              ) : (
                sessions.map((s) => (
                  <option key={s.session_id} value={s.session_id}>
                    {s.name} ({s.status.toUpperCase()} — {s.event_count} events)
                  </option>
                ))
              )}
            </select>
          </div>

          {/* Connection Badge */}
          <div className="flex items-center gap-2 self-end sm:self-center text-xs font-mono px-3 py-1.5 rounded-lg bg-slate-950/80 border border-slate-800">
            <span
              className={`w-2 h-2 rounded-full ${
                isConnected ? "bg-emerald-400 animate-pulse" : "bg-slate-500"
              }`}
            ></span>
            <span className={isConnected ? "text-emerald-400 font-semibold" : "text-slate-500"}>
              {isConnected ? "WS Stream Live" : "WS Disconnected"}
            </span>
          </div>
        </div>

        {/* Right: Trigger Live Demo Action */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full lg:w-auto">
          <select
            value={selectedScenario}
            onChange={(e) => setSelectedScenario(e.target.value)}
            disabled={isTriggeringDemo}
            className="bg-slate-950 border border-slate-700/80 rounded-lg px-3 py-2 text-xs font-mono text-amber-300 focus:outline-none focus:ring-2 focus:ring-amber-500/50"
          >
            <option value="retrieval_failure">Scenario 1: Stale Refund Policy (Retrieval)</option>
            <option value="tool_failure">Scenario 2: Truncated Lint Output (Tool)</option>
            <option value="coordination_failure">Scenario 3: Delegation Loop (Coordination)</option>
          </select>

          <button
            type="button"
            onClick={handleRunDemo}
            disabled={isTriggeringDemo}
            className="px-4 py-2 rounded-lg bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 font-mono text-xs font-bold shadow-lg shadow-emerald-500/10 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {isTriggeringDemo ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin"></span>
                Streaming Live Events...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Simulate Live Agent Run
              </>
            )}
          </button>
        </div>
      </div>

      {/* Main Execution Canvas */}
      {isLoadingSessions ? (
        <LoadingState message="Connecting to live agent runtime..." subtext="Initialising WebSocket event hub" />
      ) : !currentSession ? (
        <div className="flex flex-col items-center justify-center min-h-[350px] border border-dashed border-slate-800 rounded-xl p-8 text-center bg-slate-950/40">
          <p className="text-slate-300 font-mono text-sm font-semibold mb-2">No Active Session Selected</p>
          <p className="text-slate-500 font-mono text-xs max-w-md mb-4">
            Click &ldquo;Simulate Live Agent Run&rdquo; above to launch a real-time AI agent execution session and observe events streaming live.
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          {/* Top Session Status Info Banner */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-sm">
            <div>
              <h2 className="text-sm font-bold text-slate-100 font-mono flex items-center gap-2">
                <span>{currentSession.name}</span>
                <span className="text-[10px] font-normal px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
                  ID: {currentSession.session_id.slice(0, 8)}...
                </span>
              </h2>
              <p className="text-xs text-slate-400 mt-1">{currentSession.description}</p>
            </div>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleDiagnoseOnDemand}
                disabled={isDiagnosingManual}
                className="px-3 py-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 font-mono text-xs font-bold transition-all flex items-center gap-1.5 disabled:opacity-50"
              >
                {isDiagnosingManual ? (
                  <>
                    <span className="w-3 h-3 border-2 border-amber-300 border-t-transparent rounded-full animate-spin"></span>
                    Diagnosing...
                  </>
                ) : (
                  <>
                    <svg className="w-3.5 h-3.5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    Diagnose Now
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Dynamic Execution Graph */}
          {(() => {
            const activeGraph = (graph && graph.nodes && graph.nodes.length > 0) ? graph : activeDiagnosis?.graph || null;
            return (
              <div className="flex flex-col gap-2">
                <h3 className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider flex items-center justify-between">
                  <span>Reconstructed Execution Graph</span>
                  <span className="text-slate-500 text-[10px] font-normal">
                    {activeGraph ? `${activeGraph.nodes.length} nodes, ${activeGraph.edges.length} edges` : "Awaiting nodes..."}
                  </span>
                </h3>

                {activeGraph ? (
                  <TraceGraph
                    graph={activeGraph}
                    diagnosis={activeDiagnosis?.diagnosis}
                    anomalies={activeDiagnosis?.anomalies}
                    criticalPath={activeDiagnosis?.critical_path}
                  />
                ) : (
                  <div className="min-h-[300px] bg-slate-950 border border-slate-800 rounded-xl p-8 flex flex-col items-center justify-center gap-3 text-center">
                    <span className="w-5 h-5 border-2 border-sky-400 border-t-transparent rounded-full animate-spin"></span>
                    <p className="text-slate-300 font-mono text-sm font-semibold">Awaiting Live Stream Events...</p>
                    <p className="text-slate-500 font-mono text-xs max-w-md">
                      Graph nodes will appear dynamically as events are emitted by the agent execution runtime.
                    </p>
                  </div>
                )}
              </div>
            );
          })()}

          {/* Root Cause Diagnosis Card */}
          {activeDiagnosis && (
            <div className="flex flex-col gap-2 animate-in fade-in slide-in-from-bottom-4 duration-300">
              <h3 className="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider">
                Causal Root Cause Diagnosis & Suggested Patch
              </h3>
              <DiagnosisCard diagnosis={activeDiagnosis.diagnosis} />
            </div>
          )}
        </div>
      )}
    </div>
  );
};
