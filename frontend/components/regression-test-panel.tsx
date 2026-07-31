"use client";

import React, { useEffect, useState } from "react";
import { predictGNNRegression, runRegressionTest } from "../lib/api";
import { GNNPredictionResponse, RegressionExecutionResult, RegressionTest } from "../types/tracemind";

interface RegressionTestPanelProps {
  regressionTest: RegressionTest | null;
  traceId?: string | null;
  onGenerate: () => void;
  isLoading?: boolean;
}

export const RegressionTestPanel: React.FC<RegressionTestPanelProps> = ({
  regressionTest,
  traceId,
  onGenerate,
  isLoading = false,
}) => {
  const [copied, setCopied] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"gnn" | "runner" | "spec">("gnn");
  const [isRunningLiveTest, setIsRunningLiveTest] = useState<boolean>(false);
  const [isPredictingGNN, setIsPredictingGNN] = useState<boolean>(false);
  const [executionResult, setExecutionResult] = useState<RegressionExecutionResult | null>(null);
  const [gnnResult, setGNNResult] = useState<GNNPredictionResponse | null>(null);
  const [visibleLogCount, setVisibleLogCount] = useState<number>(0);
  const [runError, setRunError] = useState<string | null>(null);

  // Auto-fetch GNN prediction when traceId changes or when panel is mounted
  useEffect(() => {
    setExecutionResult(null);
    setGNNResult(null);
    setVisibleLogCount(0);
    setRunError(null);

    if (traceId) {
      handlePredictGNN();
    }
  }, [traceId]);

  const handlePredictGNN = async () => {
    if (!traceId) return;
    setIsPredictingGNN(true);
    try {
      const gnnRes = await predictGNNRegression(traceId);
      setGNNResult(gnnRes);
    } catch (err: unknown) {
      // Non-fatal fallback error
      console.warn("GNN prediction error:", err);
    } finally {
      setIsPredictingGNN(false);
    }
  };

  const handleRunLiveTest = async () => {
    if (!traceId) return;
    setIsRunningLiveTest(true);
    setRunError(null);
    setVisibleLogCount(0);
    setActiveTab("runner");

    try {
      if (!regressionTest) {
        onGenerate();
      }

      const result = await runRegressionTest(traceId);
      setExecutionResult(result);

      let currentLine = 0;
      const interval = setInterval(() => {
        currentLine++;
        setVisibleLogCount(currentLine);
        if (currentLine >= result.logs.length) {
          clearInterval(interval);
          setIsRunningLiveTest(false);
        }
      }, 120);
    } catch (err: unknown) {
      setRunError(err instanceof Error ? err.message : String(err));
      setIsRunningLiveTest(false);
    }
  };

  const handleCopy = async () => {
    if (!regressionTest) return;
    try {
      await navigator.clipboard.writeText(JSON.stringify(regressionTest, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div className="flex flex-col gap-5 bg-slate-900/90 border border-slate-800 rounded-xl p-5 sm:p-6 shadow-2xl backdrop-blur-md">
      {/* Top Header & Actions Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <div>
          <div className="flex items-center gap-2.5 flex-wrap">
            <h3 className="text-base font-bold font-mono text-slate-100 flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-violet-400 animate-pulse"></span>
              GNN Regression Intelligence Engine
            </h3>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-violet-500/15 text-violet-300 border border-violet-500/30 uppercase tracking-wider">
              Heterogeneous Graph Transformer (HGT)
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Vector Memory Bank Active
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Self-learning Graph Neural Network predicts structural failure risk, vulnerable node masks, and GNNExplainer subgraphs.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5 flex-wrap self-start lg:self-auto">
          <button
            type="button"
            onClick={handlePredictGNN}
            disabled={isPredictingGNN || !traceId}
            className="px-4 py-2 rounded-lg bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-mono text-xs font-bold shadow-lg shadow-violet-500/20 transition-all flex items-center gap-2 disabled:opacity-50"
          >
            {isPredictingGNN ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                <span>GNN Forward Pass...</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 01-2 2h-1a2 2 0 01-2-2v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                <span>🧠 Run GNN Inference</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={handleRunLiveTest}
            disabled={isRunningLiveTest || isLoading || !traceId}
            className="px-3.5 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-mono text-xs font-bold shadow-lg transition-all flex items-center gap-1.5 disabled:opacity-50"
          >
            {isRunningLiveTest ? (
              <>
                <span className="w-3 h-3 border-2 border-slate-950 border-t-transparent rounded-full animate-spin"></span>
                <span>Running...</span>
              </>
            ) : (
              <>
                <span>▶ Run CI Sandbox</span>
              </>
            )}
          </button>

          {regressionTest && (
            <button
              type="button"
              onClick={handleCopy}
              className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-mono text-xs font-semibold border border-slate-700 transition-colors flex items-center gap-1.5"
            >
              {copied ? (
                <span className="text-emerald-400 font-bold flex items-center gap-1">
                  ✓ Copied JSON
                </span>
              ) : (
                <span>JSON Spec</span>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Mode Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800/60 pb-2 flex-wrap">
        <button
          type="button"
          onClick={() => setActiveTab("gnn")}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-bold transition-all flex items-center gap-2 ${
            activeTab === "gnn"
              ? "bg-violet-500/15 text-violet-300 border border-violet-500/30 shadow-sm"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <span>🧠 GNN Neural Predictor</span>
          {gnnResult && (
            <span className="px-1.5 py-0.2 rounded bg-violet-500/20 text-[10px] text-violet-300">
              {(gnnResult.regression_probability * 100).toFixed(0)}% Risk
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("runner")}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-bold transition-all flex items-center gap-2 ${
            activeTab === "runner"
              ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <span>⚡ Live CI Sandbox</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("spec")}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-bold transition-all flex items-center gap-2 ${
            activeTab === "spec"
              ? "bg-indigo-500/15 text-indigo-400 border border-indigo-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
          </svg>
          <span>📄 JSON Spec</span>
        </button>
      </div>

      {/* Error Banner */}
      {runError && (
        <div className="p-4 rounded-lg bg-rose-950/40 border border-rose-900/50 text-xs font-mono text-rose-300">
          ⚠️ Execution Error: {runError}
        </div>
      )}

      {/* TAB 1: GNN Neural Predictor */}
      {activeTab === "gnn" && (
        <div className="flex flex-col gap-4">
          {isPredictingGNN && (
            <div className="flex flex-col items-center justify-center p-8 bg-slate-950 rounded-lg border border-slate-800 font-mono text-xs text-violet-400 animate-pulse">
              Running Heterogeneous Graph Transformer (HGT) forward pass & GNNExplainer...
            </div>
          )}

          {!isPredictingGNN && gnnResult && (
            <div className="flex flex-col gap-4">
              {/* KPI Prediction Metrics */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 flex flex-col gap-1">
                  <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">Regression Risk</span>
                  <span className="text-sm font-mono font-bold text-rose-400 flex items-center gap-1">
                    {(gnnResult.regression_probability * 100).toFixed(1)}%
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">P(reg) via GNN Head</span>
                </div>

                <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 flex flex-col gap-1">
                  <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">Predicted Category</span>
                  <span className="text-sm font-mono font-bold text-violet-300">
                    {gnnResult.failure_category}
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">15-Class Softmax</span>
                </div>

                <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 flex flex-col gap-1">
                  <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">Model Confidence</span>
                  <span className="text-sm font-mono font-bold text-emerald-400">
                    {(gnnResult.confidence_score * 100).toFixed(1)}%
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">HGT Latency {gnnResult.execution_time_ms}ms</span>
                </div>

                <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 flex flex-col gap-1">
                  <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">Predicted Root Cause</span>
                  <span className="text-sm font-mono font-bold text-amber-400">
                    Node &apos;{gnnResult.predicted_root_cause_node_id}&apos;
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">Max Vulnerability</span>
                </div>
              </div>

              {/* Natural Language GNN Explanation */}
              <div className="p-4 rounded-lg bg-violet-950/20 border border-violet-900/40 font-mono text-xs text-violet-200 leading-relaxed">
                <div className="text-[11px] font-bold text-violet-400 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-violet-400"></span>
                  GNN Intelligence Diagnosis & Grounded Patch
                </div>
                <p className="text-slate-300 mb-2">{gnnResult.explanation}</p>
                <div className="p-2.5 rounded bg-slate-950 border border-violet-900/50 text-[11px] text-emerald-300 font-mono">
                  <span className="text-slate-400 uppercase font-bold">Suggested Fix ({gnnResult.suggested_fix.type}):</span> {gnnResult.suggested_fix.diff}
                </div>
              </div>

              {/* Vulnerable Node Heatmap & GNNExplainer Subgraph */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Vulnerability Heatmap */}
                <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 flex flex-col gap-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider">
                      Node Vulnerability Heatmap
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">HGT Layer Attention</span>
                  </div>
                  <div className="flex flex-col gap-2">
                    {gnnResult.vulnerable_nodes.map((node) => (
                      <div
                        key={node.node_id}
                        className={`p-2.5 rounded-lg border flex items-center justify-between ${
                          node.is_root_cause_candidate
                            ? "bg-amber-950/20 border-amber-500/40 text-amber-300"
                            : "bg-slate-900/60 border-slate-800 text-slate-300"
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold text-xs">Node {node.node_id}</span>
                          {node.is_root_cause_candidate && (
                            <span className="px-1.5 py-0.2 rounded text-[9px] bg-amber-500/20 text-amber-300 font-bold">
                              ROOT CAUSE
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="w-20 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                            <div
                              className="bg-gradient-to-r from-amber-500 to-rose-500 h-1.5 rounded-full"
                              style={{ width: `${node.vulnerability_score * 100}%` }}
                            ></div>
                          </div>
                          <span className="font-mono text-xs font-bold min-w-[40px] text-right">
                            {(node.vulnerability_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* GNNExplainer Subgraph & FAISS Memory Bank */}
                <div className="flex flex-col gap-4">
                  {/* GNNExplainer Subgraph Mask */}
                  <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 flex flex-col gap-2">
                    <span className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-indigo-400"></span>
                      GNNExplainer Subgraph Mask
                    </span>
                    <p className="text-[11px] font-mono text-slate-400">
                      Minimal subgraph isolating failure root node & causal dependencies:
                    </p>
                    <div className="p-2.5 rounded bg-slate-900 border border-slate-800 font-mono text-xs text-indigo-300">
                      <div>Nodes: [{gnnResult.explanation_subgraph_nodes.join(", ")}]</div>
                      <div>Edges: [{gnnResult.explanation_subgraph_edges.join(", ")}]</div>
                    </div>
                  </div>

                  {/* FAISS Vector Memory Bank Match */}
                  <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 flex flex-col gap-2">
                    <span className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-teal-400"></span>
                      Graph Memory Bank K-NN Match
                    </span>
                    <div className="flex items-center gap-2 flex-wrap">
                      {gnnResult.similar_historical_traces.map((motif, i) => (
                        <span
                          key={i}
                          className="px-2.5 py-1 rounded bg-teal-950/40 border border-teal-800 text-teal-300 text-[11px] font-mono font-bold"
                        >
                          🔍 {motif}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Live CI Sandbox Runner */}
      {activeTab === "runner" && (
        <div className="flex flex-col gap-4">
          {!executionResult && !isRunningLiveTest && (
            <div className="flex flex-col items-center justify-center p-8 rounded-lg border border-dashed border-slate-800 bg-slate-950/40 text-center">
              <p className="text-slate-200 font-mono text-sm font-semibold mb-1">
                Live Test Suite Ready
              </p>
              <button
                type="button"
                onClick={handleRunLiveTest}
                className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-mono text-xs font-bold transition-all mt-2"
              >
                Launch Sandbox Execution
              </button>
            </div>
          )}

          {executionResult && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex flex-col gap-0.5">
                <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">Test Status</span>
                <span className="text-xs font-mono font-bold text-emerald-400 flex items-center gap-1">
                  ✓ {executionResult.status}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex flex-col gap-0.5">
                <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">Pass Rate</span>
                <span className="text-xs font-mono font-bold text-slate-200">
                  {(executionResult.pass_rate * 100).toFixed(0)}% ({executionResult.passed_assertions}/{executionResult.total_assertions})
                </span>
              </div>
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex flex-col gap-0.5">
                <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">Sandbox Latency</span>
                <span className="text-xs font-mono font-bold text-indigo-400">
                  {executionResult.execution_time_ms} ms
                </span>
              </div>
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex flex-col gap-0.5">
                <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">Verification</span>
                <span className="text-xs font-mono font-bold text-teal-400">
                  PASSED & GUARDED
                </span>
              </div>
            </div>
          )}

          {(executionResult || isRunningLiveTest) && (
            <div className="flex flex-col gap-2">
              <div className="relative rounded-lg border border-slate-800 bg-slate-950 overflow-hidden shadow-inner font-mono text-xs text-slate-300">
                <div className="p-4 max-h-[260px] overflow-auto leading-relaxed flex flex-col gap-1.5 scrollbar-thin scrollbar-thumb-slate-800">
                  {executionResult?.logs.slice(0, visibleLogCount > 0 ? visibleLogCount : executionResult.logs.length).map((logLine, idx) => (
                    <div key={idx} className="flex items-start gap-2 font-mono text-slate-300">
                      <span className="select-none text-slate-600 shrink-0">&gt;</span>
                      <span className="break-all">{logLine}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: JSON Spec Artifact */}
      {activeTab === "spec" && (
        <div className="flex flex-col gap-3">
          {regressionTest ? (
            <div className="relative rounded-lg border border-slate-800 bg-slate-950 overflow-hidden shadow-inner">
              <div className="max-h-[400px] overflow-auto p-4 font-mono text-xs text-slate-300 leading-relaxed scrollbar-thin scrollbar-thumb-slate-800">
                <pre className="whitespace-pre-wrap break-words">
                  {JSON.stringify(regressionTest, null, 2)}
                </pre>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center p-8 bg-slate-950 rounded-lg border border-slate-800 font-mono text-xs text-slate-400">
              Click &ldquo;JSON Spec&rdquo; above to generate test artifact.
            </div>
          )}
        </div>
      )}
    </div>
  );
};
