import {
  FullDiagnosisResponse,
  RegressionTest,
} from "../types/tracemind";

export const MOCK_DIAGNOSES: Record<string, FullDiagnosisResponse> = {
  retrieval_failure: {
    diagnosis: {
      failure_category: "Retrieval",
      confidence: 0.88,
      root_cause_node_id: "node_2",
      evidence_node_ids: ["node_2", "node_3", "node_7", "node_9"],
      explanation:
        "The agent retrieved a stale refund policy document from 2023 (`policy-refund-2023-v2`) instead of the current 2025 policy. While the agent's downstream reasoning logic was internally coherent, it operated on invalid premises, leading to an incorrect denial of a valid 45-day refund request.",
      suggested_fix: {
        type: "prompt_patch",
        target: "search_knowledge_base tool prompt & retrieval filter",
        diff: `--- a/prompts/retrieval_filter.txt
+++ b/prompts/retrieval_filter.txt
@@ -1,4 +1,5 @@
-search_knowledge_base(query)
+search_knowledge_base(query, filter={"effective_year": 2025})
+# ENFORCE: Filter out deprecated policy documents before returning search results.`,
      },
      grounded: true,
    },
    graph: {
      nodes: [
        { id: "node_1", type: "plan", content: "Plan refund verification", highlight: "critical_path" },
        { id: "node_2", type: "tool_call", content: "search_knowledge_base(stale 2023 policy)", highlight: "root_cause" },
        { id: "node_3", type: "observation", content: "Retrieved 2023 policy", highlight: "evidence" },
        { id: "node_4", type: "reasoning", content: "Reasoning over retrieved 30-day limit", highlight: "critical_path" },
        { id: "node_5", type: "tool_call", content: "lookup_order(C-90421)", highlight: "normal" },
        { id: "node_6", type: "observation", content: "Order age = 45 days", highlight: "normal" },
        { id: "node_7", type: "reasoning", content: "45 days > 30 days limit -> Deny", highlight: "evidence" },
        { id: "node_8", type: "decision", content: "Decision: DENY", highlight: "critical_path" },
        { id: "node_9", type: "final_answer", content: "Final Answer: Refund denied", highlight: "evidence" },
      ],
      edges: [
        { from: "node_1", to: "node_2", highlight: "critical_path" },
        { from: "node_2", to: "node_3", highlight: "evidence" },
        { from: "node_3", to: "node_4", highlight: "evidence" },
        { from: "node_4", to: "node_5", highlight: "normal" },
        { from: "node_5", to: "node_6", highlight: "normal" },
        { from: "node_4", to: "node_7", highlight: "evidence" },
        { from: "node_6", to: "node_7", highlight: "normal" },
        { from: "node_7", to: "node_8", highlight: "critical_path" },
        { from: "node_8", to: "node_9", highlight: "evidence" },
      ],
    },
    anomalies: [
      {
        node_id: "node_2",
        anomaly_type: "low_relevance",
        details: "Document retrieved was policy-refund-2023-v2 (dated 2023-03-15) with low relevance score 0.42.",
        severity_score: 0.85,
      },
    ],
    critical_path: ["node_1", "node_2", "node_4", "node_7", "node_8", "node_9"],
  },
  tool_failure: {
    diagnosis: {
      failure_category: "Tool",
      confidence: 0.92,
      root_cause_node_id: "node_5",
      evidence_node_ids: ["node_5", "node_6", "node_7", "node_12"],
      explanation:
        "The `lint_analyze` tool returned a truncated partial response (45% completeness) due to rate limiting (`rate_limit_degraded`). The agent failed to detect the truncation flag and mistakenly concluded that `UserService.java` was bug-free, leading it to misdiagnose the issue as a controller-level problem.",
      suggested_fix: {
        type: "tool_schema_fix",
        target: "lint_analyze response schema validator",
        diff: `--- a/tools/lint_analyze.py
+++ b/tools/lint_analyze.py
@@ -10,4 +10,7 @@
-return response.body
+if response.metadata.get("response_truncated"):
+    raise ToolExecutionError("Tool response truncated by server rate limit. Retry required.")
+return response.body`,
      },
      grounded: true,
    },
    graph: {
      nodes: [
        { id: "node_1", type: "plan", content: "Plan bug fix", highlight: "critical_path" },
        { id: "node_2", type: "tool_call", content: "code_search(UserService.java)", highlight: "normal" },
        { id: "node_3", type: "observation", content: "Found UserService.java", highlight: "normal" },
        { id: "node_4", type: "reasoning", content: "Analyze UserService.java", highlight: "critical_path" },
        { id: "node_5", type: "tool_call", content: "lint_analyze(truncated 45%)", highlight: "root_cause" },
        { id: "node_6", type: "observation", content: "Partial lint output", highlight: "evidence" },
        { id: "node_7", type: "reasoning", content: "Concluded UserService is clean", highlight: "evidence" },
        { id: "node_8", type: "tool_call", content: "code_search(UserController.java)", highlight: "normal" },
        { id: "node_9", type: "observation", content: "UserController code", highlight: "normal" },
        { id: "node_10", type: "reasoning", content: "Blame UserController", highlight: "critical_path" },
        { id: "node_11", type: "decision", content: "Decision: Modify UserController", highlight: "critical_path" },
        { id: "node_12", type: "final_answer", content: "Suggested wrong fix", highlight: "evidence" },
      ],
      edges: [
        { from: "node_1", to: "node_2", highlight: "normal" },
        { from: "node_2", to: "node_3", highlight: "normal" },
        { from: "node_3", to: "node_4", highlight: "critical_path" },
        { from: "node_4", to: "node_5", highlight: "evidence" },
        { from: "node_5", to: "node_6", highlight: "evidence" },
        { from: "node_6", to: "node_7", highlight: "evidence" },
        { from: "node_7", to: "node_8", highlight: "normal" },
        { from: "node_8", to: "node_9", highlight: "normal" },
        { from: "node_7", to: "node_10", highlight: "critical_path" },
        { from: "node_10", to: "node_11", highlight: "critical_path" },
        { from: "node_11", to: "node_12", highlight: "evidence" },
      ],
    },
    anomalies: [
      {
        node_id: "node_5",
        anomaly_type: "error",
        details: "Tool execution encountered rate_limit_degraded error with response_truncated=true.",
        severity_score: 0.95,
      },
    ],
    critical_path: ["node_1", "node_4", "node_5", "node_7", "node_10", "node_11", "node_12"],
  },
  coordination_failure: {
    diagnosis: {
      failure_category: "Coordination",
      confidence: 0.95,
      root_cause_node_id: "node_3",
      evidence_node_ids: ["node_3", "node_6", "node_8", "node_12"],
      explanation:
        "A multi-agent circular dependency occurred between `ResearchAgent` and `AnalysisAgent`. `ResearchAgent` required market segment analysis to normalize Azure pricing, while `AnalysisAgent` required complete raw pricing data before starting segment analysis. The orchestrator failed to break the cycle, resulting in a timeout.",
      suggested_fix: {
        type: "guardrail_addition",
        target: "orchestrator loop-detection guardrail",
        diff: `--- a/orchestrator/router.py
+++ b/orchestrator/router.py
@@ -15,3 +15,6 @@
+if detect_circular_dependency(agent_history):
+    logger.warn("Circular delegation cycle detected between sub-agents.")
+    return fallback_break_cycle(agent_history)`,
      },
      grounded: true,
    },
    graph: {
      nodes: [
        { id: "node_1", type: "plan", content: "Plan market research", highlight: "critical_path" },
        { id: "node_2", type: "delegation", content: "Delegate to ResearchAgent", highlight: "normal" },
        { id: "node_3", type: "observation", content: "Needs market context", highlight: "root_cause" },
        { id: "node_4", type: "reasoning", content: "Delegate to AnalysisAgent", highlight: "critical_path" },
        { id: "node_5", type: "delegation", content: "Delegate to AnalysisAgent", highlight: "evidence" },
        { id: "node_6", type: "observation", content: "Needs raw pricing data", highlight: "evidence" },
        { id: "node_7", type: "reasoning", content: "Cycle iteration 2", highlight: "critical_path" },
        { id: "node_8", type: "delegation", content: "Re-delegate ResearchAgent", highlight: "evidence" },
        { id: "node_9", type: "observation", content: "Still needs market context", highlight: "normal" },
        { id: "node_10", type: "delegation", content: "Re-delegate AnalysisAgent", highlight: "normal" },
        { id: "node_11", type: "observation", content: "Empty result returned", highlight: "normal" },
        { id: "node_12", type: "decision", content: "TIMEOUT (60s)", highlight: "evidence" },
      ],
      edges: [
        { from: "node_1", to: "node_2", highlight: "normal" },
        { from: "node_2", to: "node_3", highlight: "evidence" },
        { from: "node_3", to: "node_4", highlight: "critical_path" },
        { from: "node_4", to: "node_5", highlight: "evidence" },
        { from: "node_5", to: "node_6", highlight: "evidence" },
        { from: "node_6", to: "node_7", highlight: "critical_path" },
        { from: "node_7", to: "node_8", highlight: "evidence" },
        { from: "node_8", to: "node_9", highlight: "normal" },
        { from: "node_9", to: "node_10", highlight: "normal" },
        { from: "node_10", to: "node_11", highlight: "normal" },
        { from: "node_11", to: "node_12", highlight: "evidence" },
      ],
    },
    anomalies: [
      {
        node_id: "node_3",
        anomaly_type: "cycle",
        details: "Sub-agent ResearchAgent requested precondition context owned by AnalysisAgent.",
        severity_score: 0.98,
      },
    ],
    critical_path: ["node_1", "node_3", "node_4", "node_6", "node_7", "node_12"],
  },
};

export const MOCK_REGRESSION_TESTS: Record<string, RegressionTest> = {
  retrieval_failure: {
    trace_id: "retrieval_failure",
    trace_name: "Retrieval Failure — Stale Refund Policy",
    failure_category: "Retrieval",
    root_cause_node_id: "node_2",
    minimal_inputs: {
      user_query: "I bought a laptop 45 days ago and it's defective. Can I get a refund?",
      customer_id: "C-90421",
      order_id: "ORD-78234",
    },
    recorded_tool_outputs: [
      {
        tool_name: "search_knowledge_base",
        document_id: "policy-refund-2023-v2",
        retrieved_content: "Refund Policy (Effective March 2023) — Electronics purchases may be returned within 30 calendar days.",
      },
    ],
    assertion: {
      failure_category: "Retrieval",
      root_cause_pattern: "stale_document_retrieval_2023_v2",
    },
  },
  tool_failure: {
    trace_id: "tool_failure",
    trace_name: "Tool Failure — Truncated Lint Output",
    failure_category: "Tool",
    root_cause_node_id: "node_5",
    minimal_inputs: {
      task: "Find and fix the NullPointerException in UserService.java",
      file: "src/main/java/com/app/service/UserService.java",
    },
    recorded_tool_outputs: [
      {
        tool_name: "lint_analyze",
        status: "rate_limit_degraded",
        response_truncated: true,
        response_completeness: 0.45,
      },
    ],
    assertion: {
      failure_category: "Tool",
      root_cause_pattern: "truncated_tool_output_unhandled",
    },
  },
  coordination_failure: {
    trace_id: "coordination_failure",
    trace_name: "Coordination Failure — Delegation Loop",
    failure_category: "Coordination",
    root_cause_node_id: "node_3",
    minimal_inputs: {
      task: "Research competitor pricing for Q3 report and produce summary",
      sub_agents: ["ResearchAgent", "AnalysisAgent"],
    },
    recorded_tool_outputs: [
      {
        source_agent: "ResearchAgent",
        flag: "needs_market_context",
      },
      {
        source_agent: "AnalysisAgent",
        flag: "needs_pricing_data",
      },
    ],
    assertion: {
      failure_category: "Coordination",
      root_cause_pattern: "circular_subagent_delegation_loop",
    },
  },
};
