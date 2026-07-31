import React from "react";
import { useReveal } from "./RevealContext";
import { Check } from "lucide-react";
import clsx from "clsx";

const STEPS = [
  { phase: "overlay", label: "Building execution graph" },
  { phase: "dim", label: "Tracing dependencies" },
  { phase: "evidence", label: "Finding evidence" },
  { phase: "root_cause", label: "Locating root cause" },
  { phase: "summary", label: "Preparing report" },
];

const PHASE_ORDER = ["pending", "overlay", "dim", "evidence", "edges", "camera", "root_cause", "summary", "timeline", "complete"];

export function InvestigationStepIndicator() {
  const { phase } = useReveal();
  const currentPhaseIndex = PHASE_ORDER.indexOf(phase);

  return (
    <div className="mt-4 flex flex-col gap-2.5">
      {STEPS.map((step, idx) => {
        const stepIndex = PHASE_ORDER.indexOf(step.phase);
        const isComplete = currentPhaseIndex > stepIndex;
        const isActive = currentPhaseIndex >= stepIndex - 1 && !isComplete;

        return (
          <div
            key={idx}
            className={clsx(
              "flex items-center justify-between text-xs font-sans transition-all duration-300",
              isComplete ? "text-text-primary font-medium" : isActive ? "text-text-primary font-medium" : "text-text-secondary opacity-60"
            )}
          >
            <div className="flex items-center gap-2.5">
              <span className="w-4 h-4 flex items-center justify-center shrink-0">
                {isComplete ? (
                  <Check size={13} className="text-color-safeguard stroke-[2.5]" />
                ) : isActive ? (
                  <span className="w-1.5 h-1.5 rounded-full bg-color-evidence animate-pulse" />
                ) : (
                  <span className="w-1.5 h-1.5 rounded-full border border-text-secondary opacity-50" />
                )}
              </span>
              <span className="text-xs">{step.label}</span>
            </div>
            <span className="w-3 h-3 flex items-center justify-center">
              {isComplete && <Check size={12} className="text-color-safeguard" />}
              {isActive && <span className="w-1 h-1 rounded-full bg-color-evidence" />}
            </span>
          </div>
        );
      })}
    </div>
  );
}
