"""Pydantic data models for TraceMind."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Node types
# ---------------------------------------------------------------------------
class NodeType(str, Enum):
    PLAN = "plan"
    TOOL_CALL = "tool_call"
    OBSERVATION = "observation"
    REASONING = "reasoning"
    DECISION = "decision"
    DELEGATION = "delegation"
    FINAL_ANSWER = "final_answer"


# ---------------------------------------------------------------------------
# Trace primitives
# ---------------------------------------------------------------------------
class TraceNode(BaseModel):
    id: str
    type: NodeType
    timestamp: str  # ISO-8601
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    reads_from: List[str] = Field(default_factory=list)


class Trace(BaseModel):
    id: str
    name: str
    description: str
    nodes: List[TraceNode]
    expected_failure_category: str = ""  # for verification


class TraceSummary(BaseModel):
    id: str
    name: str
    description: str


# ---------------------------------------------------------------------------
# Analysis types
# ---------------------------------------------------------------------------
class AnomalyFlag(BaseModel):
    node_id: str
    anomaly_type: str  # e.g. "high_latency", "low_relevance", "cycle", "error"
    details: str
    severity_score: float = 0.0  # 0–1


class RootCauseCandidate(BaseModel):
    node_id: str
    divergence_score: float
    evidence_node_ids: List[str]
    critical_path: List[str]


# ---------------------------------------------------------------------------
# Diagnosis types
# ---------------------------------------------------------------------------
class SuggestedFix(BaseModel):
    type: str  # prompt_patch | tool_schema_fix | retry_policy | guardrail_addition
    target: str
    diff: str


class DiagnosisResult(BaseModel):
    failure_category: str
    confidence: float
    root_cause_node_id: str
    evidence_node_ids: List[str]
    explanation: str
    suggested_fix: SuggestedFix
    grounded: bool = True


class FullDiagnosisResponse(BaseModel):
    """Returned to the frontend from POST /diagnose."""
    diagnosis: DiagnosisResult
    graph: Dict[str, Any]  # serialised networkx graph (nodes + edges)
    anomalies: List[AnomalyFlag]
    critical_path: List[str]


# ---------------------------------------------------------------------------
# Regression test artifact
# ---------------------------------------------------------------------------
class RegressionAssertion(BaseModel):
    failure_category: str
    root_cause_pattern: str


class RegressionTest(BaseModel):
    trace_id: str
    trace_name: str
    failure_category: str
    root_cause_node_id: str
    minimal_inputs: Dict[str, Any]
    recorded_tool_outputs: List[Dict[str, Any]]
    assertion: RegressionAssertion
    replay_status: Optional[str] = "ready"
    replay_logs: Optional[List[str]] = Field(default_factory=list)


class AssertionDetail(BaseModel):
    name: str
    status: str  # PASSED | FAILED | SKIPPED
    duration_ms: float
    detail: Optional[str] = None


class RegressionExecutionResult(BaseModel):
    trace_id: str
    test_name: str
    status: str  # PASSED | FAILED
    baseline_status: str
    patched_status: str
    execution_time_ms: float
    pass_rate: float
    total_assertions: int
    passed_assertions: int
    assertion_details: List[AssertionDetail]
    logs: List[str]


class NodeVulnerability(BaseModel):
    node_id: str
    vulnerability_score: float  # [0, 1]
    attention_weight: float    # [0, 1]
    is_root_cause_candidate: bool


class GNNPredictionResponse(BaseModel):
    trace_id: str
    engine_version: str
    regression_probability: float  # [0, 1]
    failure_probability: float     # [0, 1]
    failure_category: str
    failure_severity: float        # [0, 1]
    confidence_score: float        # [0, 1]
    predicted_root_cause_node_id: str
    vulnerable_nodes: List[NodeVulnerability]
    explanation_subgraph_nodes: List[str]
    explanation_subgraph_edges: List[str]
    similar_historical_traces: List[str]
    explanation: str
    suggested_fix: SuggestedFix
    execution_time_ms: float



