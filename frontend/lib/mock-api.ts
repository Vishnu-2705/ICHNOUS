import {
  FullDiagnosisResponse,
  RegressionTest,
  Trace,
  TraceSummary,
} from "../types/tracemind";
import { MOCK_DIAGNOSES, MOCK_REGRESSION_TESTS } from "../mocks/diagnoses";
import { MOCK_TRACES, MOCK_TRACE_SUMMARIES } from "../mocks/traces";

export async function mockGetTraces(): Promise<TraceSummary[]> {
  await new Promise((res) => setTimeout(res, 200));
  return MOCK_TRACE_SUMMARIES;
}

export async function mockGetTrace(id: string): Promise<Trace> {
  await new Promise((res) => setTimeout(res, 250));
  const trace = MOCK_TRACES[id];
  if (!trace) {
    throw new Error(`Trace '${id}' not found.`);
  }
  return trace;
}

export async function mockDiagnoseTrace(id: string): Promise<FullDiagnosisResponse> {
  await new Promise((res) => setTimeout(res, 600));
  const diagnosis = MOCK_DIAGNOSES[id];
  if (!diagnosis) {
    throw new Error(`Diagnosis for trace '${id}' not found.`);
  }
  return diagnosis;
}

export async function mockGenerateRegressionTest(id: string): Promise<RegressionTest> {
  await new Promise((res) => setTimeout(res, 400));
  const test = MOCK_REGRESSION_TESTS[id];
  if (!test) {
    throw new Error(`Regression test for trace '${id}' not found.`);
  }
  return test;
}
