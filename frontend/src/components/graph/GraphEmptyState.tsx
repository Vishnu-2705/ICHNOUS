import React from "react";

export function GraphEmptyState() {
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center bg-bg-canvas text-center p-8 z-10 pointer-events-none">
      <div className="max-w-md">
        <h2 className="font-display font-bold text-2xl mb-2 text-text-primary">AI failures leave clues.</h2>
        <p className="text-text-secondary">Select a Case to begin.</p>
      </div>
    </div>
  );
}
