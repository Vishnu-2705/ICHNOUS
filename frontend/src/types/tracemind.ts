// Canonical TypeScript transport models for ICHNOUS / TraceMind

export type NodeType =
  | "plan"
  | "tool_call"
  | "observation"
  | "reasoning"
  | "decision"
  | "delegation"
  | "final_answer";

export type EventType =
  | "planning"
  | "llm_call"
  | "llm_response"
  | "tool_call"
  | "tool_response"
  | "observation"
  | "reasoning"
  | "decision"
  | "delegation"
  | "memory_read"
  | "memory_write"
  | "error"
  | "final_answer"
  | "custom";

export type SessionStatus =
  | "created"
  | "running"
  | "completing"
  | "completed"
  | "failed"
  | "expired";

export interface TraceNode {
  id: string;
  type: NodeType;
  timestamp: string;
  content: string;
  metadata: Record<string, unknown>;
  reads_from: string[];
}

export interface TraceEvent {
  event_id: string;
  event_type: EventType;
  timestamp: string;
  content: string;
  metadata: Record<string, unknown>;
  reads_from: string[];
  parent_event_id?: string;
  agent_id?: string;
  sequence_number?: number;
}

export interface TraceSession {
  session_id: string;
  name: string;
  description: string;
  status: SessionStatus;
  created_at: string;
  updated_at: string;
  finished_at?: string;
  events: TraceEvent[];
  event_count: number;
  agent_ids: string[];
  tags: Record<string, string>;
  diagnosis?: DiagnosisResult;
  full_diagnosis?: FullDiagnosisResponse;
  error?: string;
  ttl_seconds: number;
}

export interface SessionSummary {
  session_id: string;
  name: string;
  description: string;
  status: SessionStatus;
  event_count: number;
  created_at: string;
  updated_at: string;
  agent_ids: string[];
  tags: Record<string, string>;
}

export interface PaginatedSessions {
  items: SessionSummary[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
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
  status?: string;
  created_at?: string;
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

export interface VerificationResult {
  verified: boolean;
  verification_status: string;
  confidence_boost: number;
  execution_output: string;
}

export interface DiagnosisResult {
  failure_category: string;
  confidence: number;
  root_cause_node_id: string;
  evidence_node_ids: string[];
  explanation: string;
  suggested_fix: SuggestedFix;
  grounded: boolean;
  verification?: VerificationResult;
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
  replay_status?: "ready" | "running" | "passed" | "failed" | string;
  replay_logs?: string[];
}

export interface AssertionDetail {
  name: string;
  status: "PASSED" | "FAILED" | "SKIPPED" | string;
  duration_ms: number;
  detail?: string;
}

export interface RegressionExecutionResult {
  trace_id: string;
  test_name: string;
  status: "PASSED" | "FAILED" | string;
  baseline_status: string;
  patched_status: string;
  execution_time_ms: number;
  pass_rate: number;
  total_assertions: number;
  passed_assertions: number;
  assertion_details: AssertionDetail[];
  logs: string[];
}

export interface NodeVulnerability {
  node_id: string;
  vulnerability_score: number;
  attention_weight: number;
  is_root_cause_candidate: boolean;
}

export interface GNNPredictionResponse {
  trace_id: string;
  engine_version: string;
  regression_probability: number;
  failure_probability: number;
  failure_category: string;
  failure_severity: number;
  confidence_score: number;
  predicted_root_cause_node_id: string;
  vulnerable_nodes: NodeVulnerability[];
  explanation_subgraph_nodes: string[];
  explanation_subgraph_edges: string[];
  similar_historical_traces: string[];
  explanation: string;
  suggested_fix: SuggestedFix;
  execution_time_ms: number;
}

export type WSMessage =
  | { type: "connected"; session_id: string; status: SessionStatus; event_count: number }
  | { type: "node_added"; node: SerializedGraphNode; edges: SerializedGraphEdge[]; event_count: number; status: SessionStatus }
  | { type: "session_status"; status: SessionStatus; error?: string }
  | { type: "diagnosis_complete"; diagnosis: FullDiagnosisResponse }
  | { type: "snapshot"; session_id: string; graph: SerializedGraph }
  | { type: "ping" }
  | { type: "error"; message: string };
