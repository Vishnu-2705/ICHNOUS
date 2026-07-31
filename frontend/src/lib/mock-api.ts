import {
  FullDiagnosisResponse,
  GNNPredictionResponse,
  RegressionExecutionResult,
  RegressionTest,
  Trace,
  TraceSummary,
} from "../types/tracemind";

export async function mockGetTraces(): Promise<TraceSummary[]> {
  return [
    { id: "trace_retrieval", name: "Pricing API Failure", description: "Stale document retrieval causing discount calculation error", status: "Investigating" },
    { id: "trace_tool_call", name: "Tool Schema Discrepancy", description: "Malformed JSON schema passed to external API", status: "Resolved" },
    { id: "trace_coordination_loop", name: "Multi-Agent Cyclic Loop", description: "Infinite delegation cycle between planner and executor", status: "Investigating" },
  ];
}

export async function mockGetTrace(id: string): Promise<Trace> {
  return {
    id,
    name: "Sample Agent Trace",
    description: "Causal trace for agent execution",
    nodes: [
      { id: "node_1", type: "plan", timestamp: "10:24:00 AM", content: "Plan execution steps", metadata: {}, reads_from: [] },
      { id: "node_2", type: "tool_call", timestamp: "10:24:01 AM", content: "Execute tool call", metadata: {}, reads_from: ["node_1"] },
      { id: "node_3", type: "observation", timestamp: "10:24:02 AM", content: "Observe tool output", metadata: {}, reads_from: ["node_2"] },
      { id: "node_4", type: "reasoning", timestamp: "10:24:03 AM", content: "Synthesize response", metadata: {}, reads_from: ["node_3"] },
    ],
  };
}

export async function mockDiagnoseTrace(id: string): Promise<FullDiagnosisResponse> {
  return {
    diagnosis: {
      failure_category: "Retrieval",
      confidence: 0.94,
      root_cause_node_id: "node_2",
      evidence_node_ids: ["node_2", "node_3"],
      explanation: "stale refund policy retrieved from knowledge base",
      suggested_fix: {
        type: "prompt_patch",
        target: "node_2_boundary",
        diff: "- return self.memories[-1]\n+ return self.memory[-1]",
      },
      grounded: true,
    },
    graph: {
      nodes: [
        { id: "node_1", type: "plan", is_critical_path: true },
        { id: "node_2", type: "tool_call", is_root_cause: true, is_critical_path: true },
        { id: "node_3", type: "observation", is_evidence: true, is_critical_path: true },
        { id: "node_4", type: "reasoning", is_critical_path: true },
      ],
      edges: [
        { source: "node_1", target: "node_2", is_critical_path: true },
        { source: "node_2", target: "node_3", is_evidence: true, is_critical_path: true },
        { source: "node_3", target: "node_4", is_critical_path: true },
      ],
    },
    anomalies: [
      { node_id: "node_2", anomaly_type: "StaleData", details: "Fetched 2023 policy instead of 2026", severity_score: 0.85 },
    ],
    critical_path: ["node_1", "node_2", "node_3", "node_4"],
  };
}

export async function mockGenerateRegressionTest(id: string): Promise<RegressionTest> {
  return {
    trace_id: id,
    trace_name: "Regression Test Spec",
    failure_category: "Retrieval",
    root_cause_node_id: "node_2",
    minimal_inputs: { query: "pricing policy 2026" },
    recorded_tool_outputs: [{ status: 200, policy: "2026_v2" }],
    assertion: {
      failure_category: "Retrieval",
      root_cause_pattern: "node_2",
    },
  };
}

export async function mockRunRegressionTest(id: string): Promise<RegressionExecutionResult> {
  return {
    trace_id: id,
    test_name: `test_${id}_regression`,
    status: "PASSED",
    baseline_status: "FAILED",
    patched_status: "PASSED",
    execution_time_ms: 245.8,
    pass_rate: 1.0,
    total_assertions: 3,
    passed_assertions: 3,
    assertion_details: [
      { name: "test_input_reproducibility", status: "PASSED", duration_ms: 45.2 },
      { name: "test_root_cause_isolation", status: "PASSED", duration_ms: 112.4 },
      { name: "test_patch_verification", status: "PASSED", duration_ms: 88.2 },
    ],
    logs: [
      "[INFO] Executing regression test harness...",
      "[INFO] Replaying baseline inputs: status=FAILED (AttributeError)",
      "[INFO] Applying patch '- return self.memories[-1] -> + return self.memory[-1]'",
      "[INFO] Replaying patched execution: status=PASSED (100% assertions passed)",
    ],
  };
}

export async function mockPredictGNNRegression(id: string): Promise<GNNPredictionResponse> {
  return {
    trace_id: id,
    engine_version: "v2.4-HeteroGraphTransformer",
    regression_probability: 0.88,
    failure_probability: 0.92,
    failure_category: "Retrieval",
    failure_severity: 0.85,
    confidence_score: 0.94,
    predicted_root_cause_node_id: "node_2",
    vulnerable_nodes: [
      { node_id: "node_2", vulnerability_score: 0.88, attention_weight: 0.75, is_root_cause_candidate: true },
      { node_id: "node_3", vulnerability_score: 0.52, attention_weight: 0.45, is_root_cause_candidate: false },
    ],
    explanation_subgraph_nodes: ["node_1", "node_2", "node_3"],
    explanation_subgraph_edges: ["node_1->node_2", "node_2->node_3"],
    similar_historical_traces: ["retrieval_failure_motif_v1"],
    explanation: "GNN predicted Retrieval anomaly at node_2 with 94% confidence",
    suggested_fix: {
      type: "prompt_patch",
      target: "node_2_boundary",
      diff: "- return self.memories[-1]\n+ return self.memory[-1]",
    },
    execution_time_ms: 120.5,
  };
}
