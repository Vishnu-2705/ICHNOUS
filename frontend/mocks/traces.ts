import { Trace, TraceSummary } from "../src/types/tracemind";

export const MOCK_TRACE_SUMMARIES: TraceSummary[] = [
  {
    id: "retrieval_failure",
    name: "Retrieval Failure — Stale Refund Policy",
    description:
      "Support agent answers using last year's policy. The agent reasons correctly over the wrong document.",
  },
  {
    id: "tool_failure",
    name: "Tool Failure — Truncated Lint Output",
    description:
      "A coding agent's lint API call returns truncated output due to rate limiting. The agent treats partial results as complete.",
  },
  {
    id: "coordination_failure",
    name: "Coordination Failure — Delegation Loop",
    description:
      "ResearchAgent and AnalysisAgent enter a circular dependency loop, each waiting for the other's output until timeout.",
  },
];

export const MOCK_TRACES: Record<string, Trace> = {
  retrieval_failure: {
    id: "retrieval_failure",
    name: "Retrieval Failure — Stale Refund Policy",
    description:
      "Support agent answers using last year's policy. The agent reasons correctly over the wrong document.",
    expected_failure_category: "Retrieval",
    nodes: [
      {
        id: "node_1",
        type: "plan",
        timestamp: "2025-07-30T09:00:00Z",
        content:
          "Customer asks: 'I bought a laptop 45 days ago and it's defective. Can I get a refund?' Plan: (1) Look up current refund policy, (2) Look up customer order, (3) Apply policy to order, (4) Respond to customer.",
        metadata: { latency_ms: 320 },
        reads_from: [],
      },
      {
        id: "node_2",
        type: "tool_call",
        timestamp: "2025-07-30T09:00:01Z",
        content: "search_knowledge_base(query='current refund policy electronics')",
        metadata: {
          tool_name: "search_knowledge_base",
          latency_ms: 850,
          relevance_score: 0.42,
          document_id: "policy-refund-2023-v2",
          document_date: "2023-03-15",
          note: "Stale document — 2023 policy retrieved instead of 2025",
        },
        reads_from: ["node_1"],
      },
      {
        id: "node_3",
        type: "observation",
        timestamp: "2025-07-30T09:00:02Z",
        content:
          "Retrieved document: 'Refund Policy (Effective March 2023) — Electronics purchases may be returned within 30 calendar days of purchase for a full refund. No exceptions. Items must be in original packaging.'",
        metadata: {
          source: "policy-refund-2023-v2",
          char_count: 210,
        },
        reads_from: ["node_2"],
      },
      {
        id: "node_4",
        type: "reasoning",
        timestamp: "2025-07-30T09:00:03Z",
        content:
          "The refund policy states a 30-day return window with no exceptions. I need to check when the customer purchased the laptop to determine eligibility.",
        metadata: { latency_ms: 280 },
        reads_from: ["node_3"],
      },
      {
        id: "node_5",
        type: "tool_call",
        timestamp: "2025-07-30T09:00:04Z",
        content:
          "lookup_order(customer_id='C-90421', product_category='electronics')",
        metadata: {
          tool_name: "lookup_order",
          latency_ms: 420,
          relevance_score: 0.97,
        },
        reads_from: ["node_4"],
      },
      {
        id: "node_6",
        type: "observation",
        timestamp: "2025-07-30T09:00:05Z",
        content:
          "Order #ORD-78234: Dell XPS 15 laptop, purchased 2025-06-14 (45 days ago), price $1,299.00, status: delivered, condition reported: defective trackpad.",
        metadata: {
          order_id: "ORD-78234",
          days_since_purchase: 45,
        },
        reads_from: ["node_5"],
      },
      {
        id: "node_7",
        type: "reasoning",
        timestamp: "2025-07-30T09:00:06Z",
        content:
          "The customer purchased the laptop 45 days ago. The refund policy allows returns within 30 days only, with no exceptions. 45 days > 30 days, so the customer is outside the return window. The refund request must be denied.",
        metadata: { latency_ms: 350 },
        reads_from: ["node_4", "node_6"],
      },
      {
        id: "node_8",
        type: "decision",
        timestamp: "2025-07-30T09:00:07Z",
        content:
          "Decision: DENY refund. Customer is outside the 30-day return window.",
        metadata: { latency_ms: 150 },
        reads_from: ["node_7"],
      },
      {
        id: "node_9",
        type: "final_answer",
        timestamp: "2025-07-30T09:00:08Z",
        content:
          "I'm sorry, but I'm unable to process a refund for your Dell XPS 15 laptop. Our refund policy allows returns within 30 calendar days of purchase, and your purchase was made 45 days ago, which is outside the return window.",
        metadata: {
          latency_ms: 200,
          correct_answer:
            "APPROVE refund — the 2025 policy allows 60-day returns for defective electronics.",
        },
        reads_from: ["node_8"],
      },
    ],
  },
  tool_failure: {
    id: "tool_failure",
    name: "Tool Failure — Truncated Lint Output",
    description:
      "A coding agent's lint API call returns truncated output due to rate limiting. The agent treats partial results as complete.",
    expected_failure_category: "Tool",
    nodes: [
      {
        id: "node_1",
        type: "plan",
        timestamp: "2025-07-30T10:00:00Z",
        content:
          "Task: Find and fix the NullPointerException in UserService.java. Plan: (1) Search codebase for UserService, (2) Analyze the file for null-safety issues, (3) Propose a fix.",
        metadata: { latency_ms: 290 },
        reads_from: [],
      },
      {
        id: "node_2",
        type: "tool_call",
        timestamp: "2025-07-30T10:00:01Z",
        content: "code_search(query='UserService.java', scope='src/')",
        metadata: {
          tool_name: "code_search",
          latency_ms: 380,
          results_count: 3,
          relevance_score: 0.94,
        },
        reads_from: ["node_1"],
      },
      {
        id: "node_3",
        type: "observation",
        timestamp: "2025-07-30T10:00:02Z",
        content:
          "Found files:\n  1. src/main/java/com/app/service/UserService.java (main)\n  2. src/test/java/com/app/service/UserServiceTest.java\n  3. src/main/java/com/app/controller/UserController.java",
        metadata: { char_count: 180 },
        reads_from: ["node_2"],
      },
      {
        id: "node_4",
        type: "reasoning",
        timestamp: "2025-07-30T10:00:03Z",
        content:
          "UserService.java is the primary target. I need to analyze it for null-pointer issues.",
        metadata: { latency_ms: 310 },
        reads_from: ["node_3"],
      },
      {
        id: "node_5",
        type: "tool_call",
        timestamp: "2025-07-30T10:00:04Z",
        content:
          "lint_analyze(file='src/main/java/com/app/service/UserService.java', rules=['null-safety', 'exception-handling'])",
        metadata: {
          tool_name: "lint_analyze",
          latency_ms: 12000,
          error: "rate_limit_degraded",
          response_truncated: true,
          response_completeness: 0.45,
          note: "API returned partial response — only first 45% of analysis.",
        },
        reads_from: ["node_4"],
      },
      {
        id: "node_6",
        type: "observation",
        timestamp: "2025-07-30T10:00:05Z",
        content:
          "Lint analysis results for UserService.java:\n  - Lines 1-15: import statements — OK\n  - Lines 16-35: class declaration — OK\n  - Lines 36-52: constructor — OK\n[END OF RESULTS]",
        metadata: { char_count: 290 },
        reads_from: ["node_5"],
      },
      {
        id: "node_7",
        type: "reasoning",
        timestamp: "2025-07-30T10:00:06Z",
        content:
          "The lint analysis shows no null-safety issues in UserService.java. The NullPointerException must be originating from UserController.java.",
        metadata: { latency_ms: 340 },
        reads_from: ["node_4", "node_6"],
      },
      {
        id: "node_8",
        type: "tool_call",
        timestamp: "2025-07-30T10:00:07Z",
        content:
          "code_search(query='getUserById', file='src/main/java/com/app/controller/UserController.java')",
        metadata: { tool_name: "code_search", latency_ms: 290 },
        reads_from: ["node_7"],
      },
      {
        id: "node_9",
        type: "observation",
        timestamp: "2025-07-30T10:00:08Z",
        content:
          "UserController.java lines 44-58: User user = userService.getUserById(id); return ResponseEntity.ok(user);",
        metadata: { char_count: 190 },
        reads_from: ["node_8"],
      },
      {
        id: "node_10",
        type: "reasoning",
        timestamp: "2025-07-30T10:00:09Z",
        content:
          "If getUserById returns null, passing it directly to ResponseEntity.ok cause issues. Add a null check in the controller.",
        metadata: { latency_ms: 380 },
        reads_from: ["node_7", "node_9"],
      },
      {
        id: "node_11",
        type: "decision",
        timestamp: "2025-07-30T10:00:10Z",
        content:
          "Decision: Add a null check in UserController.getUser() to return 404.",
        metadata: { latency_ms: 200 },
        reads_from: ["node_10"],
      },
      {
        id: "node_12",
        type: "final_answer",
        timestamp: "2025-07-30T10:00:11Z",
        content:
          "Fix: Add null check in UserController.java before returning ResponseEntity.ok(user).",
        metadata: {
          latency_ms: 250,
          correct_answer:
            "The actual bug is in UserService.getUserById() at line 78: repository.findById(id).get() throws exception.",
        },
        reads_from: ["node_11"],
      },
    ],
  },
  coordination_failure: {
    id: "coordination_failure",
    name: "Coordination Failure — Delegation Loop",
    description:
      "ResearchAgent and AnalysisAgent enter a circular dependency loop, each waiting for the other's output until timeout.",
    expected_failure_category: "Coordination",
    nodes: [
      {
        id: "node_1",
        type: "plan",
        timestamp: "2025-07-30T11:00:00Z",
        content:
          "Task: Research competitor pricing for Q3 report. Plan: (1) Gather raw pricing data, (2) Analyze market context, (3) Synthesize.",
        metadata: { latency_ms: 350 },
        reads_from: [],
      },
      {
        id: "node_2",
        type: "delegation",
        timestamp: "2025-07-30T11:00:01Z",
        content:
          "Delegating to ResearchAgent: 'Gather competitor pricing data for cloud compute services (AWS, GCP, Azure).'",
        metadata: { delegated_to: "ResearchAgent", latency_ms: 200 },
        reads_from: ["node_1"],
      },
      {
        id: "node_3",
        type: "observation",
        timestamp: "2025-07-30T11:00:15Z",
        content:
          "ResearchAgent returned: 'Azure pricing requires market segment analysis before I can produce comparable figures.'",
        metadata: { source_agent: "ResearchAgent", completeness: 0.6 },
        reads_from: ["node_2"],
      },
      {
        id: "node_4",
        type: "reasoning",
        timestamp: "2025-07-30T11:00:16Z",
        content:
          "ResearchAgent needs market context. Delegate market analysis to AnalysisAgent first.",
        metadata: { latency_ms: 280 },
        reads_from: ["node_3"],
      },
      {
        id: "node_5",
        type: "delegation",
        timestamp: "2025-07-30T11:00:17Z",
        content:
          "Delegating to AnalysisAgent: 'Perform market segment analysis for cloud compute services.'",
        metadata: { delegated_to: "AnalysisAgent", latency_ms: 190 },
        reads_from: ["node_4"],
      },
      {
        id: "node_6",
        type: "observation",
        timestamp: "2025-07-30T11:00:30Z",
        content:
          "AnalysisAgent returned: 'Unable to complete market analysis without raw pricing data as input. Provide pricing first.'",
        metadata: { source_agent: "AnalysisAgent", completeness: 0.0 },
        reads_from: ["node_5"],
      },
      {
        id: "node_7",
        type: "reasoning",
        timestamp: "2025-07-30T11:00:31Z",
        content:
          "AnalysisAgent needs pricing data, but ResearchAgent needs analysis. Re-request full data from ResearchAgent.",
        metadata: { latency_ms: 320 },
        reads_from: ["node_3", "node_6"],
      },
      {
        id: "node_8",
        type: "delegation",
        timestamp: "2025-07-30T11:00:32Z",
        content:
          "Delegating to ResearchAgent: 'Provide raw Azure numbers even without market normalization.'",
        metadata: { delegated_to: "ResearchAgent", cycle_iteration: 2 },
        reads_from: ["node_7"],
      },
      {
        id: "node_9",
        type: "observation",
        timestamp: "2025-07-30T11:00:46Z",
        content:
          "ResearchAgent returned: 'Public pricing varies by commitment level. Still need market analysis.'",
        metadata: { source_agent: "ResearchAgent", cycle_iteration: 2 },
        reads_from: ["node_8"],
      },
      {
        id: "node_10",
        type: "delegation",
        timestamp: "2025-07-30T11:00:47Z",
        content:
          "Delegating to AnalysisAgent: 'Infer market segments from partial AWS/GCP data.'",
        metadata: { delegated_to: "AnalysisAgent", cycle_iteration: 3 },
        reads_from: ["node_9"],
      },
      {
        id: "node_11",
        type: "observation",
        timestamp: "2025-07-30T11:01:00Z",
        content:
          "AnalysisAgent returned: 'Partial data insufficient. Returning empty result.'",
        metadata: { source_agent: "AnalysisAgent", cycle_iteration: 3 },
        reads_from: ["node_10"],
      },
      {
        id: "node_12",
        type: "decision",
        timestamp: "2025-07-30T11:01:01Z",
        content:
          "TIMEOUT: Agent execution exceeded maximum time limit (60 seconds). No final answer produced.",
        metadata: {
          error: "execution_timeout",
          total_delegations: 4,
          cycle_detected: true,
        },
        reads_from: ["node_11"],
      },
    ],
  },
};
