"use client";

import React, { useState } from "react";

interface SDKIntegrationModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type TabType = "langgraph" | "crewai" | "autogen" | "openai" | "custom";

const SNIPPETS: Record<TabType, { name: string; description: string; code: string }> = {
  langgraph: {
    name: "LangGraph / LangChain",
    description: "Instrument LangGraph state graphs and chains with automatic node trace linking.",
    code: `import tracemind as tm
from langgraph.graph import StateGraph, END

# Initialize TraceMind live session
with tm.Session(name="LangGraph Customer Support Run", backend_url="http://localhost:8000") as session:

    def plan_step(state):
        session.emit("planning", content=f"Processing ticket: {state['user_query']}")
        return {"status": "planned"}

    def tool_step(state):
        session.emit("tool_call", content="search_kb(query=state['user_query'])", metadata={"tool_name": "search_kb"})
        session.emit("observation", content="Retrieved policy 2023: 30 day return window")
        return {"policy": "30_day"}

    def decision_step(state):
        session.emit("reasoning", content="User purchased 45 days ago. Deny refund.")
        session.emit("final_answer", content="Deny refund request.")
        return {"response": "Denied"}

    # Run your graph...
    print("Session ID:", session.session_id)`,
  },
  crewai: {
    name: "CrewAI Multi-Agent",
    description: "Instrument CrewAI multi-agent delegation, researcher, and manager tasks.",
    code: `import tracemind as tm
from crewai import Agent, Task, Crew

with tm.Session(name="CrewAI Research Crew", backend_url="http://localhost:8000") as session:
    session.emit("planning", content="Crew Task: Market share analysis for Q3")

    # Researcher Agent Step
    session.emit(
        "delegation",
        content="Delegating data collection to ResearchAgent",
        agent_id="ResearchAgent"
    )
    session.emit(
        "tool_call",
        content="web_search('Q3 Cloud Market Shares')",
        agent_id="ResearchAgent"
    )

    # Analyst Agent Step
    session.emit(
        "delegation",
        content="Delegating synthesis to AnalysisAgent",
        agent_id="AnalysisAgent"
    )
    session.emit(
        "final_answer",
        content="Final synthesis report completed.",
        agent_id="AnalysisAgent"
    )`,
  },
  autogen: {
    name: "Microsoft AutoGen",
    description: "Instrument AutoGen ConversationalAgent and UserProxyAgent interactions.",
    code: `import tracemind as tm

with tm.Session(name="AutoGen Pair Programming", backend_url="http://localhost:8000") as session:
    session.emit("planning", content="UserProxyAgent: Fix NullPointerException in UserService.java")
    
    session.emit("tool_call", content="code_search(file='UserService.java')", metadata={"tool_name": "code_search"})
    session.emit("observation", content="Code snippet retrieved")
    
    session.emit("reasoning", content="AssistantAgent analyzing null checks...")
    session.emit("final_answer", content="Fix proposed by AssistantAgent.")`,
  },
  openai: {
    name: "OpenAI / Anthropic Assistants",
    description: "Instrument direct OpenAI function calls and Anthropic Claude tool use loops.",
    code: `import tracemind as tm
from openai import OpenAI

client = OpenAI()

with tm.Session(name="OpenAI Function Agent", backend_url="http://localhost:8000") as session:
    session.emit("planning", content="User asks about order status")

    # LLM Call
    session.emit("llm_call", content="model='gpt-4o', tools=['get_order']")
    
    # Tool Execution
    session.emit("tool_call", content="get_order(order_id='ORD-78234')", metadata={"tool_name": "get_order"})
    session.emit("observation", content="Order status: Delivered 45 days ago")
    
    # Final Response
    session.emit("final_answer", content="Your order was delivered 45 days ago.")`,
  },
  custom: {
    name: "Custom Python Agent SDK",
    description: "Minimal 5-line Python instrumentation for custom agent frameworks.",
    code: `import tracemind as tm

# Synchronous usage with context manager
with tm.Session(name="My Production Agent", backend_url="http://localhost:8000") as session:
    session.emit("planning", content="Formulating plan...")
    session.emit("tool_call", content="search_database(query='refund')", metadata={"relevance_score": 0.42})
    session.emit("observation", content="Database returned stale record")
    session.emit("reasoning", content="Evaluating policy parameters...")
    session.emit("final_answer", content="Completed run.")
    
# Diagnosis automatically runs on session exit!`,
  },
};

export const SDKIntegrationModal: React.FC<SDKIntegrationModalProps> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<TabType>("langgraph");
  const [copied, setCopied] = useState<boolean>(false);

  if (!isOpen) return null;

  const currentSnippet = SNIPPETS[activeTab];

  const handleCopy = () => {
    navigator.clipboard.writeText(currentSnippet.code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-3xl w-full p-6 shadow-2xl flex flex-col gap-6 max-h-[90vh] overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <svg className="w-5 h-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
              TraceMind Live SDK Integration Guide
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Connect your AI agent or framework to stream real-time events to the TraceMind Causal Engine
            </p>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Framework Tabs */}
        <div className="flex items-center gap-2 border-b border-slate-800 pb-3 overflow-x-auto">
          {(Object.keys(SNIPPETS) as TabType[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all whitespace-nowrap ${
                activeTab === tab
                  ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 font-bold"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              {SNIPPETS[tab].name}
            </button>
          ))}
        </div>

        {/* Snippet Description */}
        <div className="text-xs text-slate-300 bg-slate-950/50 p-3 rounded-lg border border-slate-800/60 flex items-center justify-between">
          <span>{currentSnippet.description}</span>
          <button
            onClick={handleCopy}
            className="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 font-mono text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            {copied ? (
              <>
                <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Copied!
              </>
            ) : (
              <>
                <svg className="w-3.5 h-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Copy Code
              </>
            )}
          </button>
        </div>

        {/* Code View */}
        <div className="flex-1 overflow-y-auto bg-slate-950 border border-slate-800 rounded-xl p-4 font-mono text-xs text-amber-200/90 leading-relaxed shadow-inner">
          <pre className="whitespace-pre">{currentSnippet.code}</pre>
        </div>
      </div>
    </div>
  );
};
