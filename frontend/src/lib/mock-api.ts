import {
  FullDiagnosisResponse,
  RegressionTest,
  Trace,
  TraceSummary,
} from "../types/tracemind";

export async function mockGetTraces(): Promise<TraceSummary[]> {
  return [];
}

export async function mockGetTrace(id: string): Promise<Trace> {
  throw new Error(`Mock not implemented for trace ${id}`);
}

export async function mockDiagnoseTrace(id: string): Promise<FullDiagnosisResponse> {
  throw new Error(`Mock not implemented for diagnose ${id}`);
}

export async function mockGenerateRegressionTest(id: string): Promise<RegressionTest> {
  throw new Error(`Mock not implemented for regression test ${id}`);
}
