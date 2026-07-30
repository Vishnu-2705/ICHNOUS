"use client";

import React from "react";

interface ErrorStateProps {
  title?: string;
  error: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "API Execution Failed",
  error,
  onRetry,
}) => {
  const isNetworkError =
    error.includes("Could not reach the ICHNOUS backend") ||
    error.includes("Failed to fetch") ||
    error.includes("NetworkError");

  return (
    <div className="flex flex-col items-center justify-center p-6 sm:p-8 min-h-[320px] bg-red-950/20 rounded-xl border border-red-900/50 shadow-inner text-center">
      <div className="w-12 h-12 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-400 mb-4">
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>

      <h3 className="text-red-300 font-mono font-bold text-base mb-2">
        {title}
      </h3>

      <div className="max-w-xl w-full bg-slate-950 p-4 rounded-lg border border-red-900/30 mb-4 text-left overflow-x-auto">
        <pre className="text-xs font-mono text-red-400 whitespace-pre-wrap break-words">
          {error}
        </pre>
      </div>

      {isNetworkError && (
        <div className="max-w-xl w-full p-3 rounded bg-slate-900/90 border border-slate-800 text-xs font-mono text-slate-300 mb-6 text-left">
          <span className="font-bold text-amber-400 block mb-1">Troubleshooting Steps:</span>
          <ol className="list-decimal list-inside space-y-1 text-slate-400">
            <li>Ensure the FastAPI backend is running: <code className="text-slate-200 bg-slate-950 px-1 py-0.5 rounded">cd backend && uvicorn app:app --port 8000</code></li>
            <li>Check that CORS configuration allows requests from <code className="text-slate-200 bg-slate-950 px-1 py-0.5 rounded">http://localhost:3000</code></li>
            <li>Alternatively, set <code className="text-slate-200 bg-slate-950 px-1 py-0.5 rounded">NEXT_PUBLIC_USE_MOCK_API=true</code> in <code className="text-slate-200 bg-slate-950 px-1 py-0.5 rounded">.env.local</code> to run in mock mode.</li>
          </ol>
        </div>
      )}

      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white font-mono text-xs font-semibold shadow-lg transition-colors flex items-center gap-2 focus:outline-none focus:ring-2 focus:ring-red-400"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Retry Connection
        </button>
      )}
    </div>
  );
};
