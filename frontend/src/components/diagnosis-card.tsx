"use client";

import React from "react";
import { DiagnosisResult } from "../types/tracemind";
import { SuggestedFix } from "./suggested-fix";

interface DiagnosisCardProps {
  diagnosis: DiagnosisResult;
}

export const DiagnosisCard: React.FC<DiagnosisCardProps> = ({ diagnosis }) => {
  const {
    failure_category,
    confidence,
    root_cause_node_id,
    evidence_node_ids = [],
    explanation,
    suggested_fix,
    grounded = true,
  } = diagnosis;

  // Convert 0.0-1.0 confidence float for display strictly
  const confidencePercent = Math.round(Math.max(0, Math.min(1, confidence)) * 100);

  return (
    <div className="flex flex-col gap-6 bg-slate-900/60 border border-slate-800 rounded-xl p-5 sm:p-6 shadow-xl backdrop-blur-sm">
      {/* Top Banner & Category */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono uppercase text-slate-400 font-semibold tracking-wider">
                Failure Category
              </span>
              {grounded ? (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  ✓ Grounded
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                  ⚠ Ungrounded Warning
                </span>
              )}
            </div>
            <h3 className="text-xl font-bold font-mono text-slate-100 mt-0.5">
              {failure_category}
            </h3>
          </div>
        </div>

        {/* Confidence Score Gauge */}
        <div className="flex items-center gap-3 bg-slate-950 px-4 py-2.5 rounded-xl border border-slate-800 self-start md:self-auto">
          <div className="flex flex-col items-end font-mono">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider font-medium">
              Confidence Score
            </span>
            <span className="text-lg font-bold text-amber-400">
              {confidencePercent}%
            </span>
          </div>
          <div className="w-16 bg-slate-800 h-2 rounded-full overflow-hidden">
            <div
              className="bg-gradient-to-r from-amber-500 to-emerald-400 h-full rounded-full transition-all duration-500"
              style={{ width: `${confidencePercent}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Root Cause & Evidence Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Root Cause Highlight Card */}
        <div className="bg-rose-950/20 border border-rose-900/40 rounded-xl p-4 flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-rose-400 uppercase tracking-wider">
              Identified Root Cause Node
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500 text-slate-950">
              #{root_cause_node_id}
            </span>
          </div>
          <p className="text-xs font-mono text-slate-300">
            Node <code className="text-rose-300 font-bold">#{root_cause_node_id}</code> was mathematically divergence-ranked as the initiating origin of this failure.
          </p>
        </div>

        {/* Evidence Path Card */}
        <div className="bg-amber-950/20 border border-amber-900/40 rounded-xl p-4 flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider">
              Supporting Evidence Nodes
            </span>
            <span className="text-xs font-mono font-bold text-amber-300">
              {evidence_node_ids.length} Nodes
            </span>
          </div>
          <div className="flex flex-wrap gap-1.5 mt-1">
            {evidence_node_ids.map((id) => (
              <span
                key={id}
                className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-mono font-medium"
              >
                #{id}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Natural Language Explanation */}
      <div className="flex flex-col gap-2">
        <h4 className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider">
          Diagnostic Explanation
        </h4>
        <div className="bg-slate-100 dark:bg-slate-950 p-4 rounded-xl border-2 border-slate-400 dark:border-slate-800 text-slate-950 dark:text-slate-100 text-sm leading-relaxed font-sans flex flex-col gap-3">
          {explanation.split("\n\n").length >= 2 ? (
            explanation.split("\n\n").map((part, idx) => {
              let styleClass = "text-slate-950 dark:text-slate-200 font-medium";
              if (part.includes("🔍 Root Cause")) {
                styleClass = "text-red-950 dark:text-rose-300 font-mono font-bold border-l-4 border-red-500 pl-3 py-1 bg-red-100/60 dark:bg-red-950/40 rounded-r-md";
              } else if (part.includes("💡 Technical Analysis")) {
                styleClass = "text-amber-950 dark:text-amber-300 font-sans font-bold border-l-4 border-amber-500 pl-3 py-1 bg-amber-100/60 dark:bg-amber-950/40 rounded-r-md";
              } else if (part.includes("🛠️ Recommended Fix")) {
                styleClass = "text-emerald-950 dark:text-emerald-300 font-sans font-bold border-l-4 border-emerald-600 pl-3 py-1 bg-emerald-100/60 dark:bg-emerald-950/40 rounded-r-md";
              }
              return (
                <div key={idx} className={styleClass}>
                  {part}
                </div>
              );
            })
          ) : (
            <div className="font-bold text-slate-950 dark:text-slate-100">{explanation}</div>
          )}
        </div>
      </div>

      {/* Concrete Suggested Fix */}
      {suggested_fix && (
        <div className="flex flex-col gap-2">
          <h4 className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider">
            Suggested Remediation Fix
          </h4>
          <SuggestedFix fix={suggested_fix} />
        </div>
      )}
    </div>
  );
};
