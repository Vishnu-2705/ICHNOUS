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

// ---------------------------------------------------------------------------
// Static Trace API Functions
// ---------------------------------------------------------------------------
export async function getTraces(): Promise<TraceSummary[]> {
  if (isMockEnabled()) {
    return mockGetTraces();
  }

  const baseUrl = getBaseUrl();
  try {
    const res = await fetch(`${baseUrl}/traces`, {
      headers: { Accept: "application/json" },
    });
    return await handleResponse<TraceSummary[]>(res, "Failed to fetch trace summaries");
  } catch (err: unknown) {
    if (err instanceof Error) {
      if (err.message.includes("Failed to fetch") || err.message.includes("NetworkError")) {
        throw new Error(
          `Could not reach the TraceMind backend at ${baseUrl}.\nVerify that FastAPI is running on port 8000 and CORS is enabled.`
        );
      }
      throw err;
    }
    throw new Error(String(err));
  }
}

export async function getTrace(id: string): Promise<Trace> {
  if (isMockEnabled()) {
    return mockGetTrace(id);
  }

  const baseUrl = getBaseUrl();
  const encodedId = encodeURIComponent(id);
  try {
    const res = await fetch(`${baseUrl}/traces/${encodedId}`, {
      headers: { Accept: "application/json" },
    });
    return await handleResponse<Trace>(res, `Failed to fetch trace '${id}'`);
  } catch (err: unknown) {
    if (err instanceof Error) {
      if (err.message.includes("Failed to fetch") || err.message.includes("NetworkError")) {
        throw new Error(
          `Could not reach the TraceMind backend at ${baseUrl}.\nVerify that FastAPI is running on port 8000 and CORS is enabled.`
        );
      }
      throw err;
    }
    throw new Error(String(err));
  }
}

export async function diagnoseTrace(id: string): Promise<FullDiagnosisResponse> {
  if (isMockEnabled()) {
    return mockDiagnoseTrace(id);
  }

  const baseUrl = getBaseUrl();
  const encodedId = encodeURIComponent(id);
  try {
    const res = await fetch(`${baseUrl}/traces/${encodedId}/diagnose`, {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
    });
    return await handleResponse<FullDiagnosisResponse>(res, `Failed to diagnose trace '${id}'`);
  } catch (err: unknown) {
    if (err instanceof Error) {
      if (err.message.includes("Failed to fetch") || err.message.includes("NetworkError")) {
        throw new Error(
          `Could not reach the TraceMind backend at ${baseUrl}.\nVerify that FastAPI is running on port 8000 and CORS is enabled.`
        );
      }
      throw err;
    }
    throw new Error(String(err));
  }
}

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
  } catch (err: unknown) {
    if (err instanceof Error) {
      if (err.message.includes("Failed to fetch") || err.message.includes("NetworkError")) {
        throw new Error(
          `Could not reach the TraceMind backend at ${baseUrl}.\nVerify that FastAPI is running on port 8000 and CORS is enabled.`
        );
      }
      throw err;
    }
    throw new Error(String(err));
  }
}

// ---------------------------------------------------------------------------
// Live Session API Functions
// ---------------------------------------------------------------------------
export async function getSessions(): Promise<PaginatedSessions> {
  const baseUrl = getBaseUrl();
  const res = await fetch(`${baseUrl}/sessions`, {
    headers: { Accept: "application/json" },
  });
  return await handleResponse<PaginatedSessions>(res, "Failed to fetch live sessions");
}

export async function getSession(id: string): Promise<TraceSession> {
  const baseUrl = getBaseUrl();
  const encodedId = encodeURIComponent(id);
  const res = await fetch(`${baseUrl}/sessions/${encodedId}`, {
    headers: { Accept: "application/json" },
  });
  return await handleResponse<TraceSession>(res, `Failed to fetch session '${id}'`);
}

export async function getSessionGraph(id: string): Promise<SerializedGraph> {
  const baseUrl = getBaseUrl();
  const encodedId = encodeURIComponent(id);
  const res = await fetch(`${baseUrl}/sessions/${encodedId}/graph`, {
    headers: { Accept: "application/json" },
  });
  return await handleResponse<SerializedGraph>(res, `Failed to fetch graph for session '${id}'`);
}

export async function diagnoseSession(id: string): Promise<FullDiagnosisResponse> {
  const baseUrl = getBaseUrl();
  const encodedId = encodeURIComponent(id);
  const res = await fetch(`${baseUrl}/sessions/${encodedId}/diagnose`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
  });
  return await handleResponse<FullDiagnosisResponse>(res, `Failed to diagnose session '${id}'`);
}

export async function triggerLiveDemo(scenario: string): Promise<{ status: string; scenario: string; message: string }> {
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

// ---------------------------------------------------------------------------
// GNN & Regression Execution API Functions
// ---------------------------------------------------------------------------
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
  } catch (err: unknown) {
    if (err instanceof Error) {
      if (err.message.includes("Failed to fetch") || err.message.includes("NetworkError")) {
        throw new Error(
          `Could not reach the TraceMind backend at ${baseUrl}.\nVerify that FastAPI is running on port 8000 and CORS is enabled.`
        );
      }
      throw err;
    }
    throw new Error(String(err));
  }
}

export async function predictGNNRegression(id: string): Promise<GNNPredictionResponse> {
  if (isMockEnabled()) {
    return mockPredictGNNRegression(id);
  }

  const baseUrl = getBaseUrl();
  const encodedId = encodeURIComponent(id);
  try {
    const res = await fetch(`${baseUrl}/traces/${encodedId}/gnn-predict`, {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
    });
    return await handleResponse<GNNPredictionResponse>(
      res,
      `Failed to run GNN regression prediction for trace '${id}'`
    );
  } catch (err: unknown) {
    if (err instanceof Error) {
      if (err.message.includes("Failed to fetch") || err.message.includes("NetworkError")) {
        throw new Error(
          `Could not reach the TraceMind backend at ${baseUrl}.\nVerify that FastAPI is running on port 8000 and CORS is enabled.`
        );
      }
      throw err;
    }
    throw new Error(String(err));
  }
}
