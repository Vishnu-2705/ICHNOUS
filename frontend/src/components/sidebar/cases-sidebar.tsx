"use client";

import React, { useState, useMemo, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { getTraces } from "../../lib/api";
import { AlertCircle, Loader2, Search, SlidersHorizontal, SquarePen, Inbox } from "lucide-react";

interface CasesSidebarProps {
  selectedCaseId: string | null;
  onSelectCase: (id: string) => void;
}

const isOpenCase = (c: { status?: string; id?: string; name?: string }) => {
  const st = (c.status || "").toLowerCase();
  if (["investigating", "pending", "running", "processing", "open"].includes(st)) return true;
  if (["resolved", "completed", "finished", "root cause found"].includes(st)) return false;
  
  // Fallback heuristic based on ID/Name if status field is unpopulated
  const combined = `${c.id || ""} ${c.name || ""}`.toLowerCase();
  if (combined.includes("timeout") || combined.includes("exception") || combined.includes("investigating")) return true;
  return false;
};

export function CasesSidebar({ selectedCaseId, onSelectCase }: CasesSidebarProps) {
  const [activeTab, setActiveTab] = useState<"all" | "open" | "resolved">("all");
  const [searchQuery, setSearchQuery] = useState("");

  const { data: cases, isLoading, isError, error } = useQuery({
    queryKey: ["cases"],
    queryFn: getTraces,
  });

  // Memoized Filtering Logic
  const filteredCases = useMemo(() => {
    if (!cases) return [];
    return cases.filter((c) => {
      // 1. Search Query Filter
      const matchesSearch = 
        c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.description.toLowerCase().includes(searchQuery.toLowerCase());
      if (!matchesSearch) return false;

      // 2. Tab Filter
      const open = isOpenCase(c);
      if (activeTab === "open") return open;
      if (activeTab === "resolved") return !open;
      return true; // 'all'
    });
  }, [cases, searchQuery, activeTab]);

  // Preserve Selection: Clear or select first item if current selection is filtered out
  useEffect(() => {
    if (filteredCases.length > 0) {
      const isCurrentVisible = filteredCases.some((c) => c.id === selectedCaseId);
      if (!isCurrentVisible && selectedCaseId) {
        onSelectCase(filteredCases[0].id);
      }
    }
  }, [filteredCases, selectedCaseId, onSelectCase]);

  // Dynamic Empty State message
  const emptyMessage = useMemo(() => {
    if (activeTab === "open") return "No active investigations.";
    if (activeTab === "resolved") return "No resolved investigations.";
    return "No cases found.";
  }, [activeTab]);

  return (
    <aside className="flex flex-col border-r border-border-strong bg-bg-surface z-10 h-full overflow-hidden no-scrollbar">
      {/* Header */}
      <header className="px-4 py-3 border-b border-border-strong flex items-center justify-between shrink-0">
        <h1 className="font-display font-bold text-base tracking-tight text-text-primary uppercase">ICHNOUS</h1>
        <button className="p-1 text-text-primary border border-border-subtle hover:bg-bg-canvas transition-colors">
          <SquarePen size={15} />
        </button>
      </header>

      {/* Search & Filter */}
      <div className="p-3 border-b border-border-subtle flex items-center gap-2 shrink-0">
        <div className="flex-1 flex items-center gap-2 bg-bg-canvas border border-border-subtle px-2.5 py-1.5 text-xs">
          <Search size={14} className="text-text-secondary shrink-0" />
          <input
            type="text"
            placeholder="Search cases..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-transparent border-none outline-none w-full text-text-primary placeholder:text-text-secondary font-sans text-xs"
          />
        </div>
        <button className="p-1.5 border border-border-subtle text-text-secondary hover:text-text-primary hover:bg-bg-canvas transition-colors">
          <SlidersHorizontal size={14} />
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center px-3 border-b border-border-subtle shrink-0 text-xs font-medium">
        <button
          onClick={() => setActiveTab("all")}
          className={`py-2 px-3 relative font-sans transition-colors ${
            activeTab === "all" ? "text-text-primary font-semibold" : "text-text-secondary hover:text-text-primary"
          }`}
        >
          All
          {activeTab === "all" && <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-text-primary" />}
        </button>
        <button
          onClick={() => setActiveTab("open")}
          className={`py-2 px-3 relative font-sans transition-colors ${
            activeTab === "open" ? "text-text-primary font-semibold" : "text-text-secondary hover:text-text-primary"
          }`}
        >
          Open
          {activeTab === "open" && <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-text-primary" />}
        </button>
        <button
          onClick={() => setActiveTab("resolved")}
          className={`py-2 px-3 relative font-sans transition-colors ${
            activeTab === "resolved" ? "text-text-primary font-semibold" : "text-text-secondary hover:text-text-primary"
          }`}
        >
          Resolved
          {activeTab === "resolved" && <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-text-primary" />}
        </button>
      </div>

      {/* Cases List */}
      <div className="flex-1 overflow-y-auto no-scrollbar p-3 space-y-4">
        {isLoading && (
          <div className="flex flex-col justify-center items-center h-32 p-4 text-center">
            <Loader2 className="animate-spin mb-2 text-text-secondary" size={20} />
            <p className="text-text-secondary text-xs">Loading investigations...</p>
          </div>
        )}

        {isError && (
          <div className="flex flex-col justify-center items-center p-4 text-center text-color-root-cause border border-color-root-cause bg-red-50/30">
            <AlertCircle className="mb-2" size={24} />
            <p className="text-xs font-bold">Failed to load Cases</p>
            <p className="text-[10px] mt-1 opacity-80">{error instanceof Error ? error.message : "API Error"}</p>
          </div>
        )}

        {!isLoading && !isError && (
          <>
            <div>
              <div className="text-[10px] font-display font-bold uppercase tracking-widest text-text-secondary mb-2 px-1">
                TODAY
              </div>
              <div className="space-y-2">
                {filteredCases && filteredCases.length > 0 ? (
                  filteredCases.map((c, idx) => {
                    const isSelected = c.id === selectedCaseId;
                    const isOpen = isOpenCase(c);
                    const statusText = isOpen ? "Investigating" : "Resolved";
                    const statusDotColor = isOpen ? "bg-[#F59E0B]" : "bg-[#10B981]";
                    const statusTextColor = isOpen ? "text-[#F59E0B]" : "text-[#10B981]";
                    const timeString = idx === 0 ? "10:24 AM" : idx === 1 ? "9:15 AM" : "8:42 AM";

                    return (
                      <button
                        key={c.id}
                        onClick={() => onSelectCase(c.id)}
                        className={`w-full p-3 text-left transition-all relative ${
                          isSelected
                            ? "bg-bg-surface border-2 border-border-strong shadow-[4px_4px_0px_0px_#171717] z-10"
                            : "bg-transparent border border-transparent hover:bg-bg-canvas hover:border-border-subtle"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-1">
                          <span className="font-display font-bold text-xs text-text-primary line-clamp-1">
                            {c.name}
                          </span>
                          <span className="font-mono text-[10px] text-text-secondary shrink-0">
                            {timeString}
                          </span>
                        </div>
                        <p className="text-text-secondary text-[11px] line-clamp-1 mt-0.5 font-sans">
                          {c.description}
                        </p>

                        {/* Standardized 2-state Status Indicator: Investigating (Amber) vs Resolved (Green) */}
                        <div className="flex items-center gap-1.5 mt-2">
                          <span className={`w-1.5 h-1.5 rounded-full ${statusDotColor}`} />
                          <span className={`text-[10px] font-medium font-sans ${statusTextColor}`}>
                            {statusText}
                          </span>
                        </div>
                      </button>
                    );
                  })
                ) : (
                  <div className="p-4 text-center text-xs text-text-secondary border border-border-subtle bg-bg-canvas">
                    {emptyMessage}
                  </div>
                )}
              </div>
            </div>

            {/* Empty state box at bottom of sidebar */}
            <div className="pt-2">
              <div className="border border-border-subtle p-3 bg-bg-canvas flex items-center gap-2.5">
                <Inbox size={16} className="text-text-secondary shrink-0" />
                <div>
                  <p className="text-xs font-bold text-text-primary">No investigations available?</p>
                  <p className="text-[10px] text-text-secondary">New cases will appear here.</p>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Footer Profile Icon */}
      <footer className="p-3 border-t border-border-strong flex items-center justify-between shrink-0">
        <div className="w-6 h-6 rounded-full bg-text-primary text-bg-surface flex items-center justify-center font-display text-[11px] font-bold">
          N
        </div>
      </footer>
    </aside>
  );
}
