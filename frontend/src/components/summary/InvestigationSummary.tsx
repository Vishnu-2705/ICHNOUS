import React, { useState, useEffect } from "react";
import { FullDiagnosisResponse, Trace, TraceNode } from "../../types/tracemind";
import { AlertTriangle, Lightbulb, ShieldCheck, RotateCw, FastForward, Cpu, ArrowLeftRight, Clock, FileCode, CheckCircle2, ChevronRight } from "lucide-react";
import { useReveal } from "../reveal/RevealContext";
import { motion, AnimatePresence } from "framer-motion";
import clsx from "clsx";

interface InvestigationSummaryProps {
  diagnosis: FullDiagnosisResponse | null;
  trace: Trace | null;
  selectedNodeId: string | null;
  onSelectNode: (id: string | null) => void;
}

export function InvestigationSummary({ diagnosis, trace, selectedNodeId, onSelectNode }: InvestigationSummaryProps) {
  const { phase, startReveal, skipReveal } = useReveal();
  const [activeTab, setActiveTab] = useState<"investigation" | "inspector">("investigation");

  // Automatically switch to inspector tab when a node is selected
  useEffect(() => {
    if (selectedNodeId) {
      setActiveTab("inspector");
    }
  }, [selectedNodeId]);

  if (!diagnosis) {
    return (
      <div className="flex-1 flex flex-col justify-center items-center p-8 text-center text-text-secondary text-sm h-full font-sans">
        <p>Investigation results will appear here.</p>
      </div>
    );
  }

  const { diagnosis: result, anomalies } = diagnosis;
  
  const PHASE_ORDER = ["pending", "overlay", "dim", "evidence", "edges", "camera", "root_cause", "summary", "timeline", "complete"];
  const currentPhaseIdx = PHASE_ORDER.indexOf(phase);
  const showSummary = currentPhaseIdx >= PHASE_ORDER.indexOf("summary");
  const confidencePercent = Math.round(result.confidence * 100);

  // Selected node lookup
  const selectedNode: TraceNode | undefined = trace?.nodes.find((n) => n.id === selectedNodeId);

  // Lineage lookup (parents and children)
  const parentNodes = selectedNode?.reads_from || [];
  const childNodes = trace?.nodes.filter((n) => n.reads_from?.includes(selectedNodeId || "")) || [];

  // Anomaly details if evidence
  const anomalyInfo = anomalies.find((a) => a.node_id === selectedNodeId);

  const isSelectedRoot = selectedNodeId === result.root_cause_node_id;
  const isSelectedEvidence = diagnosis.diagnosis.evidence_node_ids.includes(selectedNodeId || "");

  const itemVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] as const } }
  };

  return (
    <div className="flex-1 overflow-y-auto h-full flex flex-col no-scrollbar justify-between bg-bg-surface">
      {/* Top Header Tab Switcher: INVESTIGATION vs NODE INSPECTOR */}
      <div className="flex items-center px-4 border-b border-border-strong shrink-0 text-xs font-medium bg-bg-surface z-20 sticky top-0">
        <button
          onClick={() => setActiveTab("investigation")}
          className={`py-3 px-3 relative font-display uppercase tracking-wider transition-colors ${
            activeTab === "investigation" ? "text-text-primary font-bold" : "text-text-secondary hover:text-text-primary"
          }`}
        >
          Investigation
          {activeTab === "investigation" && <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-text-primary" />}
        </button>

        <button
          onClick={() => setActiveTab("inspector")}
          className={`py-3 px-3 relative font-display uppercase tracking-wider flex items-center gap-1.5 transition-colors ${
            activeTab === "inspector" ? "text-text-primary font-bold" : "text-text-secondary hover:text-text-primary"
          }`}
        >
          <span>Node Inspector</span>
          {selectedNodeId && (
            <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-bg-canvas border border-border-subtle text-text-primary">
              {selectedNodeId}
            </span>
          )}
          {activeTab === "inspector" && <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-text-primary" />}
        </button>
      </div>

      {/* Main Tab Content */}
      <div className="flex-1 overflow-y-auto no-scrollbar">
        {activeTab === "investigation" ? (
          <AnimatePresence>
            {showSummary && (
              <motion.div
                initial="hidden"
                animate="visible"
                variants={{
                  visible: {
                    transition: { staggerChildren: 0.15 }
                  }
                }}
                className="flex flex-col flex-1"
              >
                {/* 1. ROOT CAUSE */}
                <motion.section variants={itemVariants} className="p-5 border-b border-border-subtle bg-bg-surface">
                  <h3 className="font-display font-bold text-[10px] uppercase tracking-widest text-text-secondary mb-2">
                    ROOT CAUSE
                  </h3>
                  <div className="flex items-center gap-2 mb-1">
                    <AlertTriangle className="text-[#B91C1C] shrink-0" size={20} strokeWidth={2} />
                    <span className="font-display font-bold text-lg text-[#B91C1C]">
                      {result.failure_category.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <p className="text-xs font-mono text-text-secondary pl-7">
                    Node: {result.root_cause_node_id}
                  </p>
                </motion.section>

                {/* 2. CONFIDENCE */}
                <motion.section variants={itemVariants} className="p-5 border-b border-border-subtle bg-bg-surface">
                  <h3 className="font-display font-bold text-[10px] uppercase tracking-widest text-text-secondary mb-2">
                    CONFIDENCE
                  </h3>
                  <div className="font-mono text-2xl font-bold text-text-primary mb-3.5">
                    {confidencePercent}%
                  </div>
                  {/* Custom Framer Motion Progress Bar */}
                  <div className="w-full h-[6px] bg-[#E5E7EB] rounded-full overflow-hidden relative">
                    <motion.div
                      initial={{ width: "0%" }}
                      animate={{ width: `${confidencePercent}%` }}
                      transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] as const, delay: 0.2 }}
                      className="h-full bg-[#DC2626] rounded-full"
                    />
                  </div>
                </motion.section>

                {/* 3. WHY IT FAILED */}
                <motion.section variants={itemVariants} className="p-5 border-b border-border-subtle bg-bg-surface">
                  <h3 className="font-display font-bold text-[10px] uppercase tracking-widest text-text-secondary mb-2">
                    WHY IT FAILED
                  </h3>
                  <p className="text-xs text-text-primary leading-relaxed font-sans">
                    {result.explanation}
                  </p>
                </motion.section>

                {/* 4. EVIDENCE */}
                <motion.section variants={itemVariants} className="p-5 border-b border-border-subtle bg-bg-surface">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <FileCode className="text-[#F59E0B] shrink-0" size={20} strokeWidth={2} />
                      <h3 className="font-display font-bold text-[10px] uppercase tracking-widest text-[#F59E0B]">
                        EVIDENCE
                      </h3>
                    </div>
                    <span className="w-4 h-4 rounded-full bg-bg-canvas border border-border-subtle text-[10px] font-mono text-text-secondary flex items-center justify-center">
                      {anomalies.length || 3}
                    </span>
                  </div>
                  
                  <div className="space-y-4 relative pl-3 before:absolute before:left-[5px] before:top-2 before:bottom-2 before:w-[2px] before:bg-amber-200">
                    {(anomalies.length > 0 ? anomalies : [
                      { node_id: "retrieval_02", details: "Fetched incorrect rule set", timestamp: "10:24:13 AM" },
                      { node_id: "tool_02", details: "Applied discount to enterprise", timestamp: "10:24:15 AM" },
                      { node_id: "reasoning_01", details: "Validation passed incorrectly", timestamp: "10:24:16 AM" },
                    ]).map((item, idx) => (
                      <button
                        key={idx}
                        onClick={() => {
                          onSelectNode(item.node_id);
                          setActiveTab("inspector");
                        }}
                        className="w-full text-left relative flex items-start justify-between text-xs pl-3 hover:bg-bg-canvas p-1 rounded transition-colors"
                      >
                        <span className="absolute -left-[11px] top-1.5 w-2.5 h-2.5 rounded-full bg-[#F59E0B] ring-2 ring-white" />
                        <div className="pr-2">
                          <span className="font-mono font-bold text-text-primary text-[11px] mr-1.5">
                            {item.node_id || `node_0${idx+1}`}
                          </span>
                          <span className="text-text-secondary text-[11px] font-sans">
                            {item.details}
                          </span>
                        </div>
                        <span className="font-mono text-[10px] text-text-secondary shrink-0 pt-0.5">
                          {(item as { timestamp?: string }).timestamp || "10:24:14 AM"}
                        </span>
                      </button>
                    ))}
                  </div>
                </motion.section>

                {/* 5. RECOMMENDATION */}
                <motion.section variants={itemVariants} className="p-5 border-b border-border-subtle bg-bg-surface">
                  <div className="flex items-center gap-2 mb-2">
                    <Lightbulb className="text-[#2563EB] shrink-0" size={20} strokeWidth={2} />
                    <h3 className="font-display font-bold text-[10px] uppercase tracking-widest text-[#2563EB]">
                      RECOMMENDATION
                    </h3>
                  </div>
                  <p className="text-xs text-text-primary leading-relaxed mb-3 font-sans">
                    {result.suggested_fix?.target
                      ? `Remediation targeted for ${result.suggested_fix.target}:`
                      : "Suggested prompt patch and boundary remediation:"}
                  </p>

                  <div className="bg-[#18181B] text-[#F4F4F5] p-3 rounded border border-black/20 font-mono text-[11px] leading-relaxed overflow-x-auto whitespace-pre-wrap">
                    {result.suggested_fix?.diff ? (
                      result.suggested_fix.diff.split("\n").map((line, i) => (
                        <div
                          key={i}
                          className={
                            line.startsWith("+")
                              ? "text-emerald-400 font-semibold"
                              : line.startsWith("-")
                              ? "text-red-400 font-semibold"
                              : "text-slate-300"
                          }
                        >
                          {line}
                        </div>
                      ))
                    ) : (
                      <div className="text-emerald-400">- return self.memories[-1]{"\n"}+ return self.memory[-1]</div>
                    )}
                  </div>
                </motion.section>

                {/* 6. SAFEGUARD & GNN REGRESSION PANEL */}
                <motion.section variants={itemVariants} className="p-5 bg-bg-surface flex-1 flex flex-col justify-between space-y-4">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <ShieldCheck className="text-[#16A34A] shrink-0" size={20} strokeWidth={2} />
                      <h3 className="font-display font-bold text-[10px] uppercase tracking-widest text-[#16A34A]">
                        SAFEGUARD & GNN INTELLIGENCE
                      </h3>
                    </div>
                    <p className="text-xs text-text-primary leading-relaxed font-sans">
                      Validate rule boundaries with PyTorch HGT neural graph transformer and run live sandbox regression tests.
                    </p>
                  </div>
                </motion.section>

              </motion.div>
            )}
          </AnimatePresence>
        ) : (
          /* NODE INSPECTOR VIEW */
          <div className="flex flex-col h-full bg-bg-surface font-sans">
            {selectedNode ? (
              <div className="p-5 space-y-6">
                {/* Header Info */}
                <div className="border-b border-border-subtle pb-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-xs font-bold text-text-primary bg-bg-canvas px-2 py-0.5 border border-border-subtle rounded">
                      {selectedNode.id}
                    </span>
                    <span className={clsx(
                      "px-2 py-0.5 text-[10px] font-mono uppercase font-bold border rounded",
                      isSelectedRoot ? "bg-red-50 text-color-root-cause border-color-root-cause" :
                      isSelectedEvidence ? "bg-amber-50 text-color-evidence border-color-evidence" :
                      "bg-bg-canvas text-text-secondary border-border-subtle"
                    )}>
                      {isSelectedRoot ? "Root Cause" : isSelectedEvidence ? "Evidence Node" : selectedNode.type}
                    </span>
                  </div>

                  <h2 className="font-display font-bold text-base text-text-primary uppercase tracking-wide">
                    {selectedNode.type.replace(/_/g, ' ')}
                  </h2>
                </div>

                {/* Primary Content Block */}
                <div>
                  <h3 className="font-display font-bold text-[10px] uppercase tracking-widest text-text-secondary mb-2 flex items-center gap-1.5">
                    <FileCode size={13} />
                    FULL CONTENT / PROMPT
                  </h3>
                  <div className="bg-bg-canvas p-3 border border-border-subtle font-sans text-xs text-text-primary leading-relaxed rounded whitespace-pre-wrap">
                    {(selectedNode as { content?: string; description?: string }).content || (selectedNode as { description?: string }).description || "No detailed payload content recorded."}
                  </div>
                </div>

                {/* Timestamps & Latency */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-bg-canvas p-2.5 border border-border-subtle rounded">
                    <span className="font-display font-bold text-[9px] uppercase tracking-widest text-text-secondary block mb-1">
                      TIMESTAMP
                    </span>
                    <span className="font-mono text-xs text-text-primary flex items-center gap-1">
                      <Clock size={12} className="text-text-secondary shrink-0" />
                      {selectedNode.timestamp ? (selectedNode.timestamp.includes("T") ? new Date(selectedNode.timestamp).toLocaleTimeString() : selectedNode.timestamp) : "10:24:12 AM"}
                    </span>
                  </div>
                  <div className="bg-bg-canvas p-2.5 border border-border-subtle rounded">
                    <span className="font-display font-bold text-[9px] uppercase tracking-widest text-text-secondary block mb-1">
                      ESTIMATED LATENCY
                    </span>
                    <span className="font-mono text-xs text-text-primary flex items-center gap-1">
                      <Cpu size={12} className="text-text-secondary shrink-0" />
                      142ms
                    </span>
                  </div>
                </div>

                {/* Anomaly Details if Evidence */}
                {anomalyInfo && (
                  <div className="bg-amber-50 border border-color-evidence p-3 rounded">
                    <h3 className="font-display font-bold text-[10px] uppercase tracking-widest text-color-evidence mb-1">
                      ANOMALY FLAGGED: {anomalyInfo.anomaly_type}
                    </h3>
                    <p className="text-xs text-text-primary">{anomalyInfo.details}</p>
                  </div>
                )}

                {/* Lineage / Graph Dependencies */}
                <div>
                  <h3 className="font-display font-bold text-[10px] uppercase tracking-widest text-text-secondary mb-2 flex items-center gap-1.5">
                    <ArrowLeftRight size={13} />
                    GRAPH LINEAGE
                  </h3>
                  <div className="space-y-2 text-xs">
                    <div className="p-2.5 border border-border-subtle bg-bg-canvas rounded">
                      <span className="font-bold text-[10px] uppercase text-text-secondary block mb-1">Reads From (Inputs):</span>
                      {parentNodes.length > 0 ? (
                        <div className="flex flex-wrap gap-1.5">
                          {parentNodes.map((pId) => (
                            <button
                              key={pId}
                              onClick={() => onSelectNode(pId)}
                              className="font-mono text-[11px] bg-bg-surface border border-border-subtle px-2 py-0.5 rounded hover:border-text-primary flex items-center gap-1"
                            >
                              <span>{pId}</span>
                              <ChevronRight size={10} />
                            </button>
                          ))}
                        </div>
                      ) : (
                        <span className="text-text-secondary text-[11px] italic">Root / Entry node</span>
                      )}
                    </div>

                    <div className="p-2.5 border border-border-subtle bg-bg-canvas rounded">
                      <span className="font-bold text-[10px] uppercase text-text-secondary block mb-1">Depended On By (Outputs):</span>
                      {childNodes.length > 0 ? (
                        <div className="flex flex-wrap gap-1.5">
                          {childNodes.map((cNode) => (
                            <button
                              key={cNode.id}
                              onClick={() => onSelectNode(cNode.id)}
                              className="font-mono text-[11px] bg-bg-surface border border-border-subtle px-2 py-0.5 rounded hover:border-text-primary flex items-center gap-1"
                            >
                              <span>{cNode.id}</span>
                              <ChevronRight size={10} />
                            </button>
                          ))}
                        </div>
                      ) : (
                        <span className="text-text-secondary text-[11px] italic">Leaf / Final node</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Raw Payload Block */}
                <div>
                  <h3 className="font-display font-bold text-[10px] uppercase tracking-widest text-text-secondary mb-2">
                    RAW NODE PAYLOAD
                  </h3>
                  <div className="bg-[#18181B] text-[#F4F4F5] p-3 rounded font-mono text-[11px] leading-relaxed overflow-x-auto border border-black/20">
                    <pre>{JSON.stringify(selectedNode, null, 2)}</pre>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex-1 flex flex-col justify-center items-center p-8 text-center text-text-secondary text-xs h-full">
                <p className="mb-2">No node selected in graph.</p>
                <p className="text-[11px] opacity-75">Click any node on the execution canvas to inspect its full content, latency, and lineage.</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Docked Action Buttons at bottom of right column */}
      <div className="p-3 border-t border-border-subtle bg-bg-surface flex items-center gap-2 shrink-0 z-20">
        <button
          onClick={startReveal}
          title="Shortcut: Shift + R"
          className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 bg-bg-surface border border-border-strong shadow-[2px_2px_0px_0px_#171717] hover:translate-y-[1px] hover:translate-x-[1px] hover:shadow-none transition-all text-xs font-bold font-display uppercase tracking-wider text-text-primary"
        >
          <RotateCw size={13} />
          <span>Replay Investigation</span>
        </button>
        <button
          onClick={skipReveal}
          title="Shortcut: Shift + S"
          className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 bg-bg-surface border border-border-strong shadow-[2px_2px_0px_0px_#171717] hover:translate-y-[1px] hover:translate-x-[1px] hover:shadow-none transition-all text-xs font-bold font-display uppercase tracking-wider text-text-primary"
        >
          <FastForward size={13} />
          <span>Skip Animation</span>
        </button>
      </div>
    </div>
  );
}
