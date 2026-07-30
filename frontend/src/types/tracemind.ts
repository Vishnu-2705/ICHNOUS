// Canonical TypeScript transport models for ICHNOUS / TraceMind

export type NodeType =
  | "plan"
  | "tool_call"
  | "observation"
  | "reasoning"
  | "decision"
  | "delegation"
  | "final_answer";

export interface TraceNode {
  id: string;
  type: NodeType;
  timestamp: string;
  content: string;
  metadata: Record<string, unknown>;
  reads_from: string[];
}

export interface Trace {
  id: string;
  name: string;
  description: string;
  nodes: TraceNode[];
  expected_failure_category?: string;
}

export interface TraceSummary {
  id: string;
  name: string;
  description: string;
}

export interface AnomalyFlag {
  node_id: string;
  anomaly_type: string;
  details: string;
  severity_score: number;
}

export type SuggestedFixType =
  | "prompt_patch"
  | "tool_schema_fix"
  | "retry_policy"
  | "guardrail_addition"
  | string;

export interface SuggestedFix {
  type: SuggestedFixType;
  target: string;
  diff: string;
}

export interface DiagnosisResult {
  failure_category: string;
  confidence: number;
  root_cause_node_id: string;
  evidence_node_ids: string[];
  explanation: string;
  suggested_fix: SuggestedFix;
  grounded: boolean;
}

export interface SerializedGraphNode {
  id: string;
  type: NodeType;
  label?: string;
  content?: string;
  timestamp?: string;
  metadata?: Record<string, unknown>;
  highlight?: "root_cause" | "evidence" | "critical_path" | "normal" | string;
  is_root_cause?: boolean;
  is_evidence?: boolean;
  is_critical_path?: boolean;
  anomaly_types?: string[];
  severity_score?: number;
}

export interface SerializedGraphEdge {
  id?: string;
  source?: string;
  target?: string;
  from?: string;
  to?: string;
  highlight?: "evidence" | "critical_path" | "normal" | string;
  is_evidence?: boolean;
  is_critical_path?: boolean;
}

export interface SerializedGraph {
  nodes: SerializedGraphNode[];
  edges: SerializedGraphEdge[];
}

export interface FullDiagnosisResponse {
  diagnosis: DiagnosisResult;
  graph: SerializedGraph;
  anomalies: AnomalyFlag[];
  critical_path: string[];
}

export interface RegressionAssertion {
  failure_category: string;
  root_cause_pattern: string;
}

export interface RegressionTest {
  trace_id: string;
  trace_name: string;
  failure_category: string;
  root_cause_node_id: string;
  minimal_inputs: Record<string, unknown>;
  recorded_tool_outputs: Array<Record<string, unknown>>;
  assertion: RegressionAssertion;
}
