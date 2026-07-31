"use client";

import React, { useRef, useState } from "react";

interface SourceCodeUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAnalysisComplete: (sessionId: string) => void;
}

export function SourceCodeUploadModal({
  isOpen,
  onClose,
  onAnalysisComplete,
}: SourceCodeUploadModalProps) {
  const [framework, setFramework] = useState("langgraph");
  const [sessionName, setSessionName] = useState("Uploaded Agent Code Run");
  const [codeText, setCodeText] = useState(`import tracemind.auto
from langgraph.graph import StateGraph

def search_knowledge_base(state):
    # Tool call returning stale policy document
    return {"documents": "stale 2023 refund policy"}

def evaluate_refund(state):
    # Evaluates eligibility against retrieved document
    return {"status": "denied"}

graph = StateGraph()
graph.add_node("search_kb", search_knowledge_base)
graph.add_node("evaluate", evaluate_refund)
graph.set_entry_point("search_kb")
`);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const detectFramework = (text: string) => {
    const lower = text.toLowerCase();
    if (lower.includes("langgraph") || lower.includes("stategraph")) {
      setFramework("langgraph");
    } else if (lower.includes("crewai") || lower.includes("crew")) {
      setFramework("crewai");
    } else if (lower.includes("autogen") || lower.includes("userproxyagent")) {
      setFramework("autogen");
    } else if (lower.includes("openai")) {
      setFramework("openai");
    } else if (lower.includes("anthropic") || lower.includes("claude")) {
      setFramework("anthropic");
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadedFileName(file.name);
    setSessionName(`[File] ${file.name}`);

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      if (content) {
        setCodeText(content);
        detectFramework(content);
      }
    };
    reader.readAsText(file);
  };

  const handleRunAnalysis = async () => {
    if (!codeText.trim()) {
      setError("Please select or paste Python agent source code.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const res = await fetch("http://localhost:8000/upload/analyze-code", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code_text: codeText,
          framework,
          session_name: sessionName,
        }),
      });

      if (!res.ok) {
        throw new Error(`Upload analysis failed with status ${res.status}`);
      }

      const data = await res.json();
      onAnalysisComplete(data.session_id);
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to analyze uploaded source code.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 bg-slate-900/50 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-100">Upload & Analyze Agent Source Code</h2>
              <p className="text-xs text-slate-400">
                Select or drop your agent code files (.py, .json, .txt) for instant causal analysis
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 text-sm px-2 py-1 rounded-md hover:bg-slate-800"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">
          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-xs flex items-center gap-2">
              <svg className="w-4 h-4 text-red-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{error}</span>
            </div>
          )}

          {/* File Upload Zone */}
          <div className="p-4 border-2 border-dashed border-slate-800 hover:border-amber-500/40 rounded-xl bg-slate-950/50 flex flex-col items-center justify-center text-center transition-colors group cursor-pointer"
               onClick={() => fileInputRef.current?.click()}>
            <input
              type="file"
              ref={fileInputRef}
              accept=".py,.json,.txt,.zip"
              onChange={handleFileChange}
              className="hidden"
            />
            <div className="p-3 rounded-full bg-slate-900 border border-slate-800 text-amber-400 group-hover:scale-110 transition-transform mb-2">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <p className="text-xs font-semibold text-slate-200">
              {uploadedFileName ? `Selected: ${uploadedFileName}` : "Click to select or drop Python agent code file"}
            </p>
            <p className="text-[10px] text-slate-500 mt-0.5">Supports .py, .json, .txt (LangGraph, CrewAI, AutoGen, OpenAI/Anthropic SDKs)</p>
          </div>

          {/* Framework & Session Name Selectors */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Detected Target Framework
              </label>
              <select
                value={framework}
                onChange={(e) => setFramework(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-amber-500/50"
              >
                <option value="langgraph">LangGraph (StateGraph)</option>
                <option value="crewai">CrewAI (Agent/Crew)</option>
                <option value="autogen">AutoGen (UserProxyAgent)</option>
                <option value="openai">OpenAI SDK (Functions/Assistants)</option>
                <option value="anthropic">Anthropic Claude SDK</option>
                <option value="custom">Custom OpenTelemetry Agent</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Session Run Name
              </label>
              <input
                type="text"
                value={sessionName}
                onChange={(e) => setSessionName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-amber-500/50"
              />
            </div>
          </div>

          {/* Code Editor Area */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              File Code Contents Preview
            </label>
            <textarea
              value={codeText}
              onChange={(e) => {
                setCodeText(e.target.value);
                detectFramework(e.target.value);
              }}
              rows={8}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 font-mono text-xs text-amber-200/90 focus:outline-none focus:border-amber-500/50 leading-relaxed resize-none"
              placeholder="# File contents or paste Python code..."
            />
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-900/50 flex items-center justify-between">
          <div className="text-xs text-slate-500">
            Parses uploaded source code & constructs causal execution graph.
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleRunAnalysis}
              disabled={isSubmitting}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-slate-950 font-semibold rounded-lg text-xs shadow-lg shadow-amber-500/20 disabled:opacity-50 transition-all"
            >
              {isSubmitting ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin"></span>
                  Analyzing Code...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 fill-slate-950" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                  Analyze Uploaded Code
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
