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
    schedule(40, "dim");
    schedule(80, "evidence");
    schedule(140, "edges");
    schedule(200, "camera");
    schedule(260, "root_cause");
    schedule(320, "summary");
    schedule(360, "timeline");
    schedule(400, "complete");
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
