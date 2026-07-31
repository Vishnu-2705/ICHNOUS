import React from "react";
import { useReveal } from "../reveal/RevealContext";
import { InvestigationStepIndicator } from "../reveal/InvestigationStepIndicator";
import clsx from "clsx";

export function InvestigationOverlay() {
  const { phase } = useReveal();
  const isVisible = phase === "pending" || phase === "overlay" || phase === "dim" || phase === "evidence";

  const PHASE_ORDER = ["pending", "overlay", "dim", "evidence", "edges", "camera", "root_cause", "summary", "timeline", "complete"];
  const currentIdx = PHASE_ORDER.indexOf(phase);
  const percent = Math.min(100, Math.round(((currentIdx + 1) / PHASE_ORDER.length) * 100));

  // Compute block progress bar string
  const totalBlocks = 10;
  const filledBlocks = Math.round((percent / 100) * totalBlocks);
  const emptyBlocks = totalBlocks - filledBlocks;
  const progressBlocks = "█".repeat(filledBlocks) + "░".repeat(emptyBlocks);

  return (
    <div
      className={clsx(
        "absolute top-4 right-4 z-50 pointer-events-none transition-all duration-500 ease-in-out",
        isVisible ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-2 pointer-events-none"
      )}
    >
      <div className="bg-bg-surface border-2 border-border-strong shadow-[4px_4px_0px_0px_#171717] p-5 w-[280px] pointer-events-auto">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-display font-bold text-sm text-text-primary">
            Investigating...
          </h2>
          <span className="font-mono text-xs font-bold text-text-primary">{percent}%</span>
        </div>

        {/* Monospace progress bar */}
        <div className="bg-bg-canvas border border-border-subtle p-1.5 flex items-center justify-between font-mono text-xs text-text-primary mb-4 tracking-tighter">
          <span>{progressBlocks}</span>
          <span className="text-[10px] text-text-secondary">{percent}%</span>
        </div>

        <InvestigationStepIndicator />
      </div>
    </div>
  );
}
