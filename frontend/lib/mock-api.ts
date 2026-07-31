import {
  FullDiagnosisResponse,
  GNNPredictionResponse,
  RegressionExecutionResult,
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

export async function mockRunRegressionTest(id: string): Promise<RegressionExecutionResult> {
  await new Promise((res) => setTimeout(res, 500));
  const diag = MOCK_DIAGNOSES[id];
  const trace = MOCK_TRACES[id];
  const failureCategory = diag?.diagnosis?.failure_category || "Retrieval";
  const rootCauseNode = diag?.diagnosis?.root_cause_node_id || "node_2";
  const fixType = diag?.diagnosis?.suggested_fix?.type || "guardrail_addition";
  const fixTarget = diag?.diagnosis?.suggested_fix?.target || "system_boundary";

  return {
    trace_id: id,
    test_name: `CI Sandbox Test Suite — ${trace?.name || id}`,
    status: "PASSED",
    baseline_status: "FAILED_AS_EXPECTED",
    patched_status: "PASSED",
    execution_time_ms: 138,
    pass_rate: 1.0,
    total_assertions: 4,
    passed_assertions: 4,
    assertion_details: [
      {
        name: "Minimal Task & Tool State Injection",
        status: "PASSED",
        duration_ms: 14,
        detail: `Replayed minimal inputs & mock tool outputs for trace '${id}'`,
      },
      {
        name: "Baseline Failure Reproduction",
        status: "PASSED",
        duration_ms: 68,
        detail: `Successfully reproduced ${failureCategory} anomaly at target node '${rootCauseNode}'`,
      },
      {
        name: "Guardrail Patch Application",
        status: "PASSED",
        duration_ms: 24,
        detail: `Applied fix '${fixType}' targeting '${fixTarget}'`,
      },
      {
        name: "Patched Workflow Verification",
        status: "PASSED",
        duration_ms: 32,
        detail: "0 errors detected; workflow completed with 100% assertion match",
      },
    ],
    logs: [
      `[00:00.000] 🚀 Initializing ICHNOUS Test Sandbox for trace '${id}'...`,
      `[00:00.014] 📥 Loaded minimal task inputs & recorded tool output context.`,
      `[00:00.035] 🔴 Phase 1: Executing Baseline Unpatched Workflow...`,
      `[00:00.068] ❌ Baseline Run: Failure reproduced! (${failureCategory} anomaly at node '${rootCauseNode}').`,
      `[00:00.082] 🛡️ Phase 2: Applying Patch Guardrail ('${fixType}')...`,
      `[00:00.106] 🟢 Executing Patched Workflow in Isolated Sandbox...`,
      `[00:00.138] ✅ Patched Run: PASSED! Guardrail intercepted failure prior to execution.`,
      `[00:00.138] 🎉 VERDICT: Live Regression Test PASSED (100% assertion coverage).`,
    ],
  };
}

export async function mockPredictGNNRegression(id: string): Promise<GNNPredictionResponse> {
  await new Promise((res) => setTimeout(res, 450));
  const diag = MOCK_DIAGNOSES[id];
  const failureCategory = diag?.diagnosis?.failure_category || "Retrieval";
  const rootCauseNode = diag?.diagnosis?.root_cause_node_id || "node_2";

  return {
    trace_id: id,
    engine_version: "v2.4-HeteroGraphTransformer",
    regression_probability: 0.885,
    failure_probability: 0.912,
    failure_category: failureCategory,
    failure_severity: 0.82,
    confidence_score: 0.94,
    predicted_root_cause_node_id: rootCauseNode,
    vulnerable_nodes: [
      { node_id: rootCauseNode, vulnerability_score: 0.94, attention_weight: 0.88, is_root_cause_candidate: true },
      { node_id: "node_3", vulnerability_score: 0.62, attention_weight: 0.54, is_root_cause_candidate: false },
      { node_id: "node_7", vulnerability_score: 0.45, attention_weight: 0.38, is_root_cause_candidate: false },
    ],
    explanation_subgraph_nodes: [rootCauseNode, "node_3", "node_7"],
    explanation_subgraph_edges: [`${rootCauseNode}->node_3`, "node_3->node_7"],
    similar_historical_traces: [`${id}_motif_v1`, "golden_normal_run_v1"],
    explanation: `[GNN Intelligence Engine] Heterogeneous Graph Transformer predicted a ${failureCategory} regression risk (0.885) rooted at node '${rootCauseNode}'.`,
    suggested_fix: diag?.diagnosis?.suggested_fix || {
      type: "guardrail_addition",
      target: `node_${rootCauseNode}_boundary`,
      diff: `+ Intercept structural regression pattern at ${rootCauseNode}`,
    },
    execution_time_ms: 3.42,
  };
}


