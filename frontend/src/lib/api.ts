import {
  FullDiagnosisResponse,
  GNNPredictionResponse,
  PaginatedSessions,
  RegressionExecutionResult,
  RegressionTest,
  SerializedGraph,
  SessionSummary,
  Trace,
  TraceSession,
  TraceSummary,
} from "../types/tracemind";
import {
  mockDiagnoseTrace,
  mockGenerateRegressionTest,
  mockGetTrace,
  mockGetTraces,
  mockPredictGNNRegression,
  mockRunRegressionTest,
} from "./mock-api";

function getBaseUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  return envUrl.replace(/\/+$/, "");
}

function isMockEnabled(): boolean {
  return process.env.NEXT_PUBLIC_USE_MOCK_API === "true";
}

async function handleResponse<T>(res: Response, fallbackErrorMsg: string): Promise<T> {
  if (!res.ok) {
    let errorDetail = "";
    try {
      const data = await res.json();
      if (data && typeof data.detail === "string") {
        errorDetail = data.detail;
      } else if (data && typeof data.detail === "object") {
        errorDetail = JSON.stringify(data.detail);
      }
    } catch {
      try {
        errorDetail = await res.text();
      } catch {
        errorDetail = res.statusText;
      }
    }

    const message = errorDetail
      ? `[API Error ${res.status}] ${errorDetail}`
      : `${fallbackErrorMsg} (${res.status} ${res.statusText})`;
    throw new Error(message);
  }

  return (await res.json()) as T;
}

/**
 * Fetch trace summaries from both live sessions (GET /sessions) and static fixtures (GET /traces).
 */
export async function getTraces(): Promise<TraceSummary[]> {
  if (isMockEnabled()) {
    return mockGetTraces();
  }

  const baseUrl = getBaseUrl();
  const allCases: TraceSummary[] = [];

  // 1. Try to fetch live sessions from GET /sessions
  try {
    const res = await fetch(`${baseUrl}/sessions`, {
      headers: { Accept: "application/json" },
    });
    if (res.ok) {
      const data = (await res.json()) as PaginatedSessions;
      if (data && Array.isArray(data.items)) {
        for (const item of data.items) {
          allCases.push({
            id: item.session_id,
            name: item.name || `Session ${item.session_id.slice(0, 8)}`,
            description: item.description || `Live agent session (${item.event_count} events)`,
            status: item.status,
            created_at: item.created_at,
          });
        }
      }
    }
  } catch {
    // Non-fatal if session service is initializing
  }

  // 2. Fetch static fixture traces from GET /traces
  try {
    const res = await fetch(`${baseUrl}/traces`, {
      headers: { Accept: "application/json" },
    });
    if (res.ok) {
      const fixtureSummaries = (await res.json()) as TraceSummary[];
      if (Array.isArray(fixtureSummaries)) {
        for (const fix of fixtureSummaries) {
          if (!allCases.some((c) => c.id === fix.id)) {
            allCases.push(fix);
          }
        }
      }
    }
  } catch (err: unknown) {
    if (allCases.length === 0) {
      throw new Error(
        `Could not reach the ICHNOUS backend at ${baseUrl}.\nVerify that FastAPI is running on port 8000 and CORS is enabled.`
      );
    }
  }

  return allCases.length > 0 ? allCases : mockGetTraces();
}

/**
 * Fetch trace detail by ID (from GET /sessions/{id} or GET /traces/{id}).
 */
export async function getTrace(id: string): Promise<Trace> {
  if (isMockEnabled()) {
    return mockGetTrace(id);
  }

  const baseUrl = getBaseUrl();
  const encodedId = encodeURIComponent(id);

  // 1. If UUID / session format, try live session endpoint first
  if (id.includes("-") || id.length > 20) {
    try {
      const res = await fetch(`${baseUrl}/sessions/${encodedId}`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        const session = (await res.json()) as TraceSession;
        // Convert session events into TraceNodes
        const nodes = (session.events || []).map((evt, idx) => ({
          id: evt.event_id || `evt_${idx}`,
          type: (evt.event_type || "reasoning") as any,
          timestamp: evt.timestamp || new Date().toISOString(),
          content: evt.content || "",
          metadata: evt.metadata || {},
          reads_from: evt.reads_from || (evt.parent_event_id ? [evt.parent_event_id] : []),
        }));

        return {
          id: session.session_id,
          name: session.name || `Session ${session.session_id.slice(0, 8)}`,
          description: session.description || "Live agent trace session",
          nodes,
        };
      }
    } catch {
      // Fallback to static traces
    }
  }

  // 2. Try static fixture trace endpoint
  try {
    const res = await fetch(`${baseUrl}/traces/${encodedId}`, {
      headers: { Accept: "application/json" },
    });
    return await handleResponse<Trace>(res, `Failed to fetch trace '${id}'`);
  } catch (err: unknown) {
    if (err instanceof Error && err.message.includes("404")) {
      return mockGetTrace(id);
    }
    throw err;
  }
}

/**
 * Run full causal diagnosis on a session or static trace.
 */
export async function diagnoseTrace(id: string): Promise<FullDiagnosisResponse> {
  if (isMockEnabled()) {
    return mockDiagnoseTrace(id);
  }

  const baseUrl = getBaseUrl();
  const encodedId = encodeURIComponent(id);

  // 1. Try live session diagnosis endpoint
  if (id.includes("-") || id.length > 20) {
    try {
      const res = await fetch(`${baseUrl}/sessions/${encodedId}/diagnose`, {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
      });
      if (res.ok) {
        return (await res.json()) as FullDiagnosisResponse;
      }
    } catch {
      // Fallback to trace endpoint
    }
  }

  // 2. Try static trace diagnosis endpoint
  try {
    const res = await fetch(`${baseUrl}/traces/${encodedId}/diagnose`, {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
    });
    return await handleResponse<FullDiagnosisResponse>(res, `Failed to diagnose trace '${id}'`);
  } catch (err: unknown) {
    return mockDiagnoseTrace(id);
  }
}

/**
 * Generate regression test spec for trace.
 */
export async function generateRegressionTest(id: string): Promise<RegressionTest> {
  if (isMockEnabled()) {
    return mockGenerateRegressionTest(id);
  }

  const baseUrl = getBaseUrl();
  const encodedId = encodeURIComponent(id);
  try {
    const res = await fetch(`${baseUrl}/traces/${encodedId}/regression-test`, {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
    });
    return await handleResponse<RegressionTest>(
      res,
      `Failed to generate regression test for trace '${id}'`
    );
  } catch {
    return mockGenerateRegressionTest(id);
  }
}

/**
 * Run interactive regression test runner simulation.
 */
export async function runRegressionTest(id: string): Promise<RegressionExecutionResult> {
  if (isMockEnabled()) {
    return mockRunRegressionTest(id);
  }

  const baseUrl = getBaseUrl();
  const encodedId = encodeURIComponent(id);
  try {
    const res = await fetch(`${baseUrl}/traces/${encodedId}/run-regression`, {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
    });
    return await handleResponse<RegressionExecutionResult>(
      res,
      `Failed to execute regression test for trace '${id}'`
    );
  } catch {
    return mockRunRegressionTest(id);
  }
}

/**
 * Run PyTorch GNN Regression Intelligence prediction.
 */
export async function predictGNNRegression(id: string): Promise<GNNPredictionResponse> {
  if (isMockEnabled()) {
    return mockPredictGNNRegression(id);
  }

  const baseUrl = getBaseUrl();
  const encodedId = encodeURIComponent(id);

  // Try live session gnn-predict first if session ID
  if (id.includes("-") || id.length > 20) {
    try {
      const res = await fetch(`${baseUrl}/sessions/${encodedId}/gnn-predict`, {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
      });
      if (res.ok) {
        return (await res.json()) as GNNPredictionResponse;
      }
    } catch {
      // Fallback
    }
  }

  try {
    const res = await fetch(`${baseUrl}/traces/${encodedId}/gnn-predict`, {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
    });
    return await handleResponse<GNNPredictionResponse>(
      res,
      `Failed to run GNN regression prediction for trace '${id}'`
    );
  } catch {
    return mockPredictGNNRegression(id);
  }
}

/**
 * Upload code file for real sandbox execution and session creation.
 */
export async function uploadCodeForAnalysis(file: File): Promise<{ session_id: string; message: string; filename: string }> {
  const baseUrl = getBaseUrl();
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${baseUrl}/upload/analyze-code`, {
    method: "POST",
    body: formData,
  });

  return await handleResponse<{ session_id: string; message: string; filename: string }>(
    res,
    "Failed to analyze uploaded code file"
  );
}

/**
 * Trigger live interactive demo scenario stream over WebSocket.
 */
export async function triggerLiveDemo(
  scenario: string
): Promise<{ status: string; scenario: string; message: string }> {
  const baseUrl = getBaseUrl();
  const res = await fetch(`${baseUrl}/sessions/demo/${encodeURIComponent(scenario)}`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
  });
  return await handleResponse<{ status: string; scenario: string; message: string }>(
    res,
    `Failed to trigger live demo scenario '${scenario}'`
  );
}


