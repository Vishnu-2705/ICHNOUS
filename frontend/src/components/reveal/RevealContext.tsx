"use client";

import React, { createContext, useContext, useState, useEffect, useRef } from "react";

export type RevealPhase = 
  | "pending"    // API call active
  | "overlay"    // API finished, overlay pausing
  | "dim"        // Graph dims (200ms)
  | "evidence"   // Evidence highlights (500ms)
  | "edges"      // Edge animation (850ms)
  | "camera"     // Camera movement (1200ms)
  | "root_cause" // Root Cause pulses (1500ms)
  | "summary"    // Summary stagger (1700ms)
  | "timeline"   // Timeline sync (2000ms)
  | "complete";  // Replay available (2200ms)

interface RevealContextValue {
  phase: RevealPhase;
  startReveal: () => void;
  skipReveal: () => void;
  resetReveal: () => void;
}

const RevealContext = createContext<RevealContextValue | null>(null);

export function RevealProvider({ children }: { children: React.ReactNode }) {
  const [phase, setPhase] = useState<RevealPhase>("pending");
  const timersRef = useRef<NodeJS.Timeout[]>([]);

  const clearTimers = () => {
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];
  };

  const startReveal = () => {
    clearTimers();
    setPhase("overlay");

    const schedule = (ms: number, nextPhase: RevealPhase) => {
      timersRef.current.push(setTimeout(() => setPhase(nextPhase), ms));
    };

    schedule(0, "overlay");
    schedule(200, "dim");
    schedule(500, "evidence");
    schedule(850, "edges");
    schedule(1200, "camera"); // Camera starts
    schedule(1700, "root_cause"); // 1700ms Root cause pulse
    schedule(1900, "summary"); // 1900ms Summary stagger
    schedule(2200, "timeline"); // 2200ms Timeline sync
    schedule(2400, "complete"); // 2400ms Replay available
  };

  const skipReveal = () => {
    clearTimers();
    setPhase("complete");
  };

  const resetReveal = () => {
    clearTimers();
    setPhase("pending");
  };

  useEffect(() => {
    return clearTimers;
  }, []);

  return (
    <RevealContext.Provider value={{ phase, startReveal, skipReveal, resetReveal }}>
      {children}
    </RevealContext.Provider>
  );
}

export function useReveal() {
  const context = useContext(RevealContext);
  if (!context) throw new Error("useReveal must be used within RevealProvider");
  return context;
}
