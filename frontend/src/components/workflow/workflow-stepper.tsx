"use client";

import React from "react";
import {
  Upload,
  Network,
  AlertTriangle,
  FileCode,
  ShieldCheck,
  CheckCircle2,
  ChevronRight,
  Sparkles,
} from "lucide-react";

export type WorkflowStage =
  | "upload"
  | "graph"
  | "root_cause"
  | "diagnosis"
  | "verification"
  | "complete";

interface WorkflowStepperProps {
  currentStage: WorkflowStage;
  onSelectStage: (stage: WorkflowStage) => void;
  isVerified?: boolean;
}

const STAGES: { id: WorkflowStage; label: string; icon: React.ComponentType<{ size?: number; className?: string }> }[] = [
  { id: "upload", label: "1. Upload & Ingest", icon: Upload },
  { id: "graph", label: "2. Graph Build", icon: Network },
  { id: "root_cause", label: "3. Root Cause", icon: AlertTriangle },
  { id: "diagnosis", label: "4. AI Diagnosis", icon: FileCode },
  { id: "verification", label: "5. Patch Verify", icon: ShieldCheck },
  { id: "complete", label: "6. Verified Dashboard", icon: CheckCircle2 },
];

export const WorkflowStepper: React.FC<WorkflowStepperProps> = ({
  currentStage,
  onSelectStage,
  isVerified = true,
}) => {
  const currentIndex = STAGES.findIndex((s) => s.id === currentStage);

  return (
    <div className="w-full bg-bg-surface border-b border-border-strong px-4 py-2 flex items-center justify-between shadow-sm overflow-x-auto no-scrollbar shrink-0">
      <div className="flex items-center gap-1 min-w-max">
        {STAGES.map((stage, idx) => {
          const Icon = stage.icon;
          const isActive = stage.id === currentStage;
          const isCompleted = idx < currentIndex;

          return (
            <React.Fragment key={stage.id}>
              <button
                type="button"
                onClick={() => onSelectStage(stage.id)}
                className={`flex items-center gap-2 px-3 py-1.5 font-display text-xs font-bold transition-all border ${
                  isActive
                    ? "bg-text-primary text-bg-surface border-border-strong shadow-[2px_2px_0px_0px_#171717]"
                    : isCompleted
                    ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/30 hover:bg-emerald-500/20"
                    : "bg-bg-canvas text-text-secondary border-border-subtle hover:text-text-primary hover:border-border-strong"
                }`}
              >
                <Icon
                  size={14}
                  className={
                    isActive
                      ? "text-bg-surface"
                      : isCompleted
                      ? "text-emerald-500"
                      : "text-text-secondary"
                  }
                />
                <span>{stage.label}</span>
                {isCompleted && <CheckCircle2 size={12} className="text-emerald-500" />}
              </button>

              {idx < STAGES.length - 1 && (
                <ChevronRight size={14} className="text-border-strong opacity-40 shrink-0" />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {isVerified && (
        <div className="hidden md:flex items-center gap-1.5 px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 rounded text-emerald-600 font-display font-bold text-xs">
          <Sparkles size={13} className="animate-pulse text-emerald-500" />
          <span>VERIFIED FIX AVAILABLE</span>
        </div>
      )}
    </div>
  );
};
