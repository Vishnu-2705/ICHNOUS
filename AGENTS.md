# AGENTS.md — TraceMind Repository Guide

This file is the shared operating contract for all human contributors and coding agents working on TraceMind. It applies to the entire repository unless a deeper `AGENTS.md` overrides a specific directory.

The primary goal is to ship a reliable, demoable 24-hour hackathon MVP with minimal integration risk. Prefer a complete end-to-end diagnosis loop over production infrastructure, architectural purity, or additional features.

---

## 1. Project Summary

**Project name:** TraceMind  
**Title:** TraceMind — The Causal Debugger for Autonomous AI Systems  
**Core pitch:** Every other observability tool shows what happened. TraceMind shows why—and gives the fix.

TraceMind accepts a recorded trace of an autonomous AI-agent run and produces:

1. A reconstructed causal execution graph.
2. A single ranked root-cause node.
3. A failure category from a fixed taxonomy.
4. Structurally grounded evidence nodes and paths.
5. A confidence score.
6. A concrete suggested fix.
7. A JSON regression-test artifact that can reproduce the failure.

TraceMind is not a general monitoring platform, predictive reliability operating system, self-healing runtime, or production trace-ingestion service in this MVP. Its differentiator is deterministic structural root-cause analysis followed by one grounded LLM explanation call.

---

## 2. Hackathon Constraints

All contributors must optimize for these constraints:

- Time limit: 24 hours.
- Team size: 2 contributors.
- Architecture: one FastAPI backend and one Next.js frontend.
- Storage: in-memory dictionaries or SQLite only.
- Authentication: none.
- Cloud infrastructure: none.
- LLM calls: at most one diagnosis call per trace diagnosis.
- Data source: three hardcoded trace fixtures.
- Primary demo: raw JSON versus TraceMind diagnosis.
- Reliability: deterministic fixture results matter more than broad generalization.

Do not add Neo4j, Qdrant, Redis, Postgres, Kafka, Kubernetes, Terraform, OpenTelemetry ingestion, multi-tenant auth, billing, SOC 2 work, CI execution, vector search, model fine-tuning, or unrelated AI features.

---

## 3. Team Ownership

### Person 1 — Backend and Intelligence Engine

Person 1 owns:

- Pydantic data models.
- Three trace fixtures.
- FastAPI application and routes.
- NetworkX graph construction.
- Anomaly detection.
- Critical-path extraction.
- Backward causal walk.
- Divergence scoring and root-cause ranking.
- One LLM diagnosis call.
- LLM JSON validation and groundedness checks.
- Regression-test artifact generation.
- Backend tests and deterministic fixture verification.

Person 1 must expose the canonical REST API defined in this file. Person 1 must not require the frontend to understand NetworkX internals or backend implementation details.

### Person 2 — Frontend, Visualization, and API Integration

Person 2 owns:

- The complete Next.js single-page user interface.
- Shared TypeScript API types matching backend Pydantic schemas.
- API client and environment configuration.
- Trace selector.
- Raw JSON view.
- TraceMind graph view.
- Diagnosis card.
- Regression-test artifact viewer.
- Loading, empty, and error states.
- Mock API data for independent development.
- Frontend integration tests and demo polish.

Person 2 must not reimplement causal analysis, anomaly detection, diagnosis logic, confidence calculation, or regression generation in the browser.

### Shared Responsibility

Both contributors own:

- Freezing the API contract before parallel work.
- Keeping fixture IDs and node IDs stable.
- CORS and local development configuration.
- End-to-end testing.
- Demo rehearsal.
- Updating this file when a contract changes.

No contributor may silently change a shared schema. Any breaking contract change must be made in both backend Pydantic models and frontend TypeScript types in the same integration window.

---

## 4. System Architecture

```text
Trace fixture
    |
    v
FastAPI route
    |
    v
NetworkX graph builder
    |
    v
Deterministic structural analyzer
    |-- anomaly detection
    |-- critical path
    |-- backward causal walk
    |-- root-cause ranking
    |
    v
One grounded LLM diagnosis call
    |
    v
Schema and evidence validation
    |
    +-------------------+
    |                   |
    v                   v
Diagnosis response   Regression artifact
    |                   |
    +--------- REST ----+
              |
              v
        Next.js frontend
    | raw trace | graph | diagnosis | regression JSON |
```

The LLM is an explanation and fix-generation layer. It is not the structural root-cause detector.

---

## 5. Canonical Domain Models

Backend Pydantic models and frontend TypeScript interfaces must remain semantically equivalent.

### Node Types

Allowed values:

```text
plan
tool_call
observation
reasoning
decision
delegation
final_answer
```

Do not introduce a `retrieval` node type in the MVP. Represent retrieval as a `tool_call` and/or `observation` with metadata such as `tool_name`, `document_version`, and `relevance_score`.

### TraceNode

```json
{
  "id": "node_4",
  "type": "observation",
  "timestamp": "2026-07-30T10:00:00Z",
  "content": "Retrieved refund policy version 2025",
  "metadata": {
    "tool_name": "policy_search",
    "relevance_score": 0.31,
    "document_version": "2025",
    "status": "success"
  },
  "reads_from": ["node_3"]
}
```

Required fields:

- `id: string`
- `type: NodeType`
- `timestamp: string` in ISO-8601 format
- `content: string`
- `metadata: Record<string, unknown>`
- `reads_from: string[]`

### Trace

```json
{
  "id": "retrieval_failure",
  "name": "Stale Refund Policy",
  "description": "Support agent answers using last year's policy.",
  "nodes": [],
  "expected_failure_category": "Retrieval"
}
```

### TraceSummary

```json
{
  "id": "retrieval_failure",
  "name": "Stale Refund Policy",
  "description": "Support agent answers using last year's policy."
}
```

### AnomalyFlag

```json
{
  "node_id": "node_4",
  "anomaly_type": "low_relevance",
  "details": "Retrieval relevance score 0.31 is below threshold 0.50.",
  "severity_score": 0.82
}
```

`severity_score` is in the inclusive range `0.0` to `1.0`.

### SuggestedFix

```json
{
  "type": "guardrail_addition",
  "target": "policy retrieval step",
  "diff": "Reject documents whose effective date is older than the current policy version."
}
```

Allowed MVP fix types:

```text
prompt_patch
tool_schema_fix
retry_policy
guardrail_addition
```

### DiagnosisResult

```json
{
  "failure_category": "Retrieval",
  "confidence": 0.87,
  "root_cause_node_id": "node_4",
  "evidence_node_ids": ["node_4", "node_5", "node_7"],
  "explanation": "The retrieval step returned a stale policy. The downstream reasoning was internally consistent but based on that incorrect input.",
  "suggested_fix": {
    "type": "guardrail_addition",
    "target": "policy retrieval step",
    "diff": "Filter retrieved documents by current effective date before reasoning begins."
  },
  "grounded": true
}
```

### FullDiagnosisResponse

```json
{
  "diagnosis": {},
  "graph": {
    "nodes": [],
    "edges": []
  },
  "anomalies": [],
  "critical_path": []
}
```

### RegressionTest

```json
{
  "trace_id": "retrieval_failure",
  "trace_name": "Stale Refund Policy",
  "failure_category": "Retrieval",
  "root_cause_node_id": "node_4",
  "minimal_inputs": {
    "task": "Can I receive a refund after 30 days?",
    "current_policy_version": "2026"
  },
  "recorded_tool_outputs": [],
  "assertion": {
    "failure_category": "Retrieval",
    "root_cause_pattern": "stale or low-relevance policy document must not reach reasoning"
  }
}
```

---

## 6. Fixed Failure Taxonomy

Every diagnosis must use exactly one of these categories:

```text
Planning
Memory
Retrieval
Reasoning
Context
Hallucination
Specification
Tool
Safety
Verification
Coordination
Timeout
External API
Human
Unknown
```

The backend must reject or normalize any category outside this list. The frontend must display unknown future values safely, but it must not invent categories.

Expected fixture categories:

- Retrieval fixture: `Retrieval`
- Malformed/truncated tool result fixture: `Tool`
- Delegation loop fixture: `Coordination`

A timeout may be visible in the coordination fixture, but the intended causal category is `Coordination` because the delegation cycle occurs upstream of the timeout.

---

## 7. Trace Fixtures

Fixture IDs are API identifiers and must remain stable after integration begins.

### 7.1 `retrieval_failure`

Scenario:

- A customer-support agent receives a refund-policy question.
- The retrieval tool returns last year's policy or a stale document.
- Metadata exposes low relevance, stale version, or both.
- Downstream reasoning is correct relative to the stale input.
- The final answer is wrong.
- The root cause must be the upstream retrieval observation/tool node, not the final answer.

### 7.2 `tool_failure`

Scenario:

- A coding agent calls a search or lint tool.
- The tool returns truncated or malformed data due to simulated rate-limit degradation.
- Metadata includes a schema mismatch, truncation flag, rate-limit status, abnormal size, or related anomaly.
- Downstream reasoning incorrectly treats the result as complete.
- The root cause must be the malformed tool output or tool-call node, not the bad suggestion.

### 7.3 `coordination_failure`

Scenario:

- A multi-agent workflow delegates a task between two agents.
- A shared-state mismatch makes the agents delegate the task back and forth.
- The graph contains a detectable cycle or loop count greater than three.
- The run times out without a valid final answer.
- The root cause must be the coordination/delegation loop, not the final timeout node.

---

## 8. Backend Structural Analysis Contract

The frontend does not reproduce this algorithm, but all contributors must understand what backend output means.

### 8.1 Graph Construction

- Use `networkx.DiGraph`.
- Create one graph node per `TraceNode`.
- Create directed edges from every `reads_from` source to the dependent node.
- Preserve original trace fields as graph-node attributes.
- Reject or flag missing `reads_from` references.
- Prefer deterministic node ordering based on fixture order or timestamp.

### 8.2 Anomaly Surfacing

The backend should flag at least:

- Explicit error status.
- Abnormal latency above a hardcoded MVP threshold.
- Truncated or malformed output.
- Schema mismatch.
- Low retrieval relevance.
- Stale document/version metadata.
- Cycle or delegation loop.
- Loop iteration greater than three.
- Timeout.

### 8.3 Critical Path

The critical path is the causal path from the initial node to the failure point.

The failure point is:

- The `final_answer` node for incorrect-answer scenarios.
- The final node before an error or timeout when no final answer exists.

Return critical-path node IDs in execution order.

### 8.4 Backward Causal Walk

Starting from the failure point:

1. Walk backward through the critical path.
2. Compute a divergence score for each relevant node.
3. Surface nodes with structural anomalies.
4. Prefer the earliest upstream divergence that explains normal downstream propagation.
5. Do not automatically select the node closest to the visible failure.

### 8.5 LLM Role

The backend passes only the structurally selected candidate and connected evidence subgraph to one LLM call.

The LLM returns:

- Failure category.
- Explanation.
- Evidence IDs.
- Suggested fix.
- A proposed confidence value if the backend prompt requests it.

The backend remains authoritative for:

- Root-cause candidate selection.
- Valid node IDs.
- Evidence connectivity.
- Final groundedness.
- Confidence downgrading when citations are invalid.

### 8.6 Groundedness

A diagnosis is grounded only when:

- `root_cause_node_id` exists in the graph.
- Every evidence node exists.
- Evidence nodes are structurally connected to the root cause or relevant failure path.
- The root cause is upstream of the visible failure for the three fixtures.

Never silently accept invented evidence IDs.

---

## 9. Canonical REST API

The canonical route prefix is `/traces`, plural. Do not use `/trace` or standalone `/diagnose` routes in the integrated application.

Default backend URL:

```text
http://localhost:8000
```

### `GET /traces`

Returns:

```json
[
  {
    "id": "retrieval_failure",
    "name": "Stale Refund Policy",
    "description": "Support agent answers using last year's policy."
  }
]
```

### `GET /traces/{id}`

Returns one complete `Trace`.

Error behavior:

- `404` when fixture ID does not exist.
- JSON error body with a human-readable `detail` field.

### `POST /traces/{id}/diagnose`

Runs:

```text
graph build -> anomaly detection -> critical path -> backward walk
-> root-cause ranking -> one LLM call -> validation -> groundedness check
```

Returns `FullDiagnosisResponse`.

The backend may cache the result per fixture for demo speed and API-cost control.

### `POST /traces/{id}/regression-test`

Returns a `RegressionTest` artifact. The endpoint may reuse a cached diagnosis or run diagnosis first when required.

### Optional Health Route

A non-demo route is allowed:

```text
GET /health
```

Suggested response:

```json
{
  "status": "ok",
  "llm_configured": true
}
```

The frontend must not depend on this route to render the main page.

---

## 10. Graph Serialization Contract

NetworkX objects must never be sent directly to the frontend. Serialize the graph as:

```json
{
  "nodes": [
    {
      "id": "node_4",
      "type": "observation",
      "label": "Retrieved stale refund policy",
      "content": "Retrieved refund policy version 2025",
      "timestamp": "2026-07-30T10:00:00Z",
      "metadata": {},
      "is_root_cause": true,
      "is_evidence": true,
      "is_critical_path": true,
      "anomaly_types": ["low_relevance", "stale_document"],
      "severity_score": 0.82
    }
  ],
  "edges": [
    {
      "id": "node_3->node_4",
      "source": "node_3",
      "target": "node_4",
      "is_evidence": true,
      "is_critical_path": true
    }
  ]
}
```

Minimum required frontend fields:

For each graph node:

- `id`
- `type`
- `label` or `content`

For each graph edge:

- `source`
- `target`

Highlight fields may be supplied by the backend as shown above. When highlight fields are absent, Person 2 derives them from:

- `diagnosis.root_cause_node_id`
- `diagnosis.evidence_node_ids`
- `critical_path`
- `anomalies`

The frontend must tolerate additional fields.

---

## 11. Person 2 Module — Detailed Implementation Guide

This section is the canonical context for anyone implementing, reviewing, or continuing Person 2's work.

### 11.1 Person 2 Goal

Build a one-page interface that makes TraceMind's value obvious within five seconds:

1. Raw trace JSON looks tedious and difficult to debug.
2. TraceMind view immediately highlights the true upstream root cause.
3. The diagnosis card explains the causal chain and fix.
4. A button reveals a reusable regression-test artifact.

The UI is part of the product demonstration, not a generic admin dashboard.

### 11.2 Recommended Frontend Stack

- Next.js with App Router.
- TypeScript with strict mode enabled.
- Tailwind CSS for styling.
- React Flow for the execution graph, unless a different graph library is already working.
- Native `fetch` through one typed API-client module.
- No global state library unless integration proves it necessary.

Do not introduce Redux, GraphQL, tRPC, server actions for backend proxying, or a component library that slows delivery.

### 11.3 Person 2 Directory Contract

Recommended structure:

```text
frontend/
├── app/
│   ├── globals.css
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── trace-selector.tsx
│   ├── view-toggle.tsx
│   ├── raw-trace-view.tsx
│   ├── trace-graph.tsx
│   ├── graph-node.tsx
│   ├── diagnosis-card.tsx
│   ├── suggested-fix.tsx
│   ├── regression-test-panel.tsx
│   ├── loading-state.tsx
│   └── error-state.tsx
├── lib/
│   ├── api.ts
│   ├── graph.ts
│   ├── format.ts
│   └── mock-api.ts
├── types/
│   └── tracemind.ts
├── mocks/
│   ├── traces.ts
│   └── diagnoses.ts
├── .env.local.example
├── package.json
└── tsconfig.json
```

This is a recommended layout, not evidence that every listed file already exists. Preserve equivalent separation if the project uses different filenames.

### 11.4 Environment Configuration

Use exactly one public API URL variable:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Example `.env.local.example`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_USE_MOCK_API=false
```

Mock mode is permitted for isolated frontend work. The final demo must use the real backend.

### 11.5 TypeScript Types

Create frontend types that mirror backend schemas. Do not use `any` for API payloads.

```ts
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

export interface SuggestedFix {
  type:
    | "prompt_patch"
    | "tool_schema_fix"
    | "retry_policy"
    | "guardrail_addition"
    | string;
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
  is_root_cause?: boolean;
  is_evidence?: boolean;
  is_critical_path?: boolean;
  anomaly_types?: string[];
  severity_score?: number;
}

export interface SerializedGraphEdge {
  id?: string;
  source: string;
  target: string;
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
```

The frontend should be defensive about optional graph-display fields but strict about the core API response.

### 11.6 API Client

All network calls belong in `lib/api.ts` or an equivalent single module.

Required functions:

```ts
getTraces(): Promise<TraceSummary[]>
getTrace(id: string): Promise<Trace>
diagnoseTrace(id: string): Promise<FullDiagnosisResponse>
generateRegressionTest(id: string): Promise<RegressionTest>
```

API-client rules:

- Read the base URL from `NEXT_PUBLIC_API_URL`.
- Remove trailing slashes before joining paths.
- Check `response.ok` for every request.
- Parse FastAPI's `detail` field when available.
- Throw an `Error` with a user-readable message.
- Do not place `fetch` calls directly inside display components.
- Do not silently fall back to mock data when a real API call fails.

### 11.7 Page State

The page should own or coordinate these states:

```ts
selectedTraceId: string | null
traceList: TraceSummary[]
selectedTrace: Trace | null
diagnosis: FullDiagnosisResponse | null
regressionTest: RegressionTest | null
activeView: "raw" | "tracemind"
isLoadingTraces: boolean
isLoadingTrace: boolean
isDiagnosing: boolean
isGeneratingRegression: boolean
error: string | null
```

State transitions:

- On page load, fetch trace summaries.
- Select the first trace automatically when available.
- On trace selection, fetch the raw trace and clear the previous diagnosis and regression artifact.
- Raw view may render immediately after the trace loads.
- Clicking `Diagnose` calls the diagnosis endpoint and switches or updates the TraceMind view.
- Clicking `Generate Regression Test` calls the regression endpoint and reveals the artifact.
- A failed request must leave the rest of the page usable.

Avoid race conditions when users switch traces quickly. Either abort stale requests or confirm that the returned trace ID still matches the current selection before updating state.

### 11.8 Page Layout

Recommended desktop layout:

```text
+---------------------------------------------------------------+
| TraceMind logo/title                 trace selector            |
+---------------------------------------------------------------+
| Raw Trace | TraceMind toggle                                 |
+---------------------------------------------------------------+
|                                                               |
| Main content                                                  |
|                                                               |
| Raw mode: formatted scrolling JSON                            |
|                                                               |
| TraceMind mode:                                               |
| +---------------------------+ +-----------------------------+  |
| | Execution graph           | | Diagnosis card              |  |
| |                           | | Category / confidence       |  |
| |                           | | Explanation                 |  |
| |                           | | Suggested fix               |  |
| +---------------------------+ | Regression button           |  |
|                               +-----------------------------+  |
+---------------------------------------------------------------+
```

On narrow screens, stack the graph above the diagnosis card. Desktop presentation quality is the priority for the hackathon demo.

### 11.9 Trace Selector

The selector displays:

- Trace name.
- Optional short description.
- A stable selected value using the trace ID.

Changing the selection must:

- Clear diagnosis and regression state.
- Fetch the new raw trace.
- Preserve the active tab only when it does not create confusion; defaulting back to Raw is acceptable for the demo sequence.

### 11.10 Raw Trace View

Purpose: create intentional contrast with TraceMind.

Requirements:

- Render the complete trace as formatted JSON.
- Use a monospaced font.
- Preserve indentation.
- Use a fixed-height scrollable container.
- Do not hide nodes or simplify the raw payload.
- Keep it readable but visually dense and tedious.
- Provide a copy button only when it is quick to implement.

Do not make the raw view so polished that it weakens the product contrast.

### 11.11 TraceMind Graph View

The graph must communicate causal structure, not merely chronology.

Node visual rules:

- Root cause: red border/fill treatment and strongest emphasis.
- Evidence nodes: highlighted with a secondary strong treatment.
- Critical-path nodes: visually distinct from unrelated nodes.
- Normal nodes: subdued.
- Anomalous nodes: optional badge or indicator.
- Selected/hovered node: show content and relevant metadata.

Edge visual rules:

- Evidence-path edges: emphasized.
- Critical-path edges: visible but less strong than the root-cause evidence path.
- Other edges: subdued.
- Edge direction must be visible.

Node labels should be concise. Prefer a short label derived from `label`, then `content`, truncated for the canvas. Full content belongs in a tooltip, side panel, or node detail popover.

The graph must remain useful when backend highlight booleans are absent. Derive visual state from diagnosis and path arrays.

### 11.12 Graph Data Conversion

Create a pure helper such as:

```ts
toReactFlowElements(
  graph: SerializedGraph,
  diagnosis: DiagnosisResult,
  anomalies: AnomalyFlag[],
  criticalPath: string[]
): { nodes: Node[]; edges: Edge[] }
```

This helper should:

- Build sets for root cause, evidence, critical-path, and anomaly membership.
- Avoid repeated array scans inside render loops.
- Attach original graph data to each visual node.
- Produce deterministic output.
- Handle empty graphs without throwing.
- Ignore edges whose source or target is missing, or mark them as invalid for debugging.

Do not mix API fetching with graph transformation.

### 11.13 Diagnosis Card

Display:

- Failure-category badge.
- Confidence as a rounded percentage.
- Grounded/ungrounded status.
- Root-cause node ID.
- Plain-language explanation.
- Evidence-node list.
- Suggested-fix type.
- Suggested-fix target.
- Suggested-fix diff/instruction.
- Generate Regression Test button.

Confidence display:

```ts
Math.round(Math.max(0, Math.min(1, confidence)) * 100)
```

When `grounded` is false, clearly warn that the LLM evidence could not be fully validated. Do not hide this state.

### 11.14 Regression Test Panel

On button click:

- Show a loading state.
- Call the backend endpoint.
- Render the complete returned JSON.
- Use a monospaced, scrollable code block.
- Include a clear label such as `Generated Golden Trace Regression Artifact`.
- A copy button is useful but optional.

Do not claim the artifact has been run in CI. The demo claim is that TraceMind generated a replayable regression artifact.

### 11.15 Loading, Empty, and Error States

Required states:

- Initial trace-list loading.
- Trace loading.
- Diagnosis running.
- Regression generation running.
- No traces available.
- Backend unavailable.
- Unknown trace ID or 404.
- Invalid diagnosis payload.
- Empty graph.

Errors should be visible and actionable. Example:

```text
Could not reach the TraceMind backend at http://localhost:8000.
Verify that FastAPI is running and CORS allows the frontend origin.
```

Do not leave the page indefinitely spinning.

### 11.16 Mock Development Mode

Person 2 must be able to work before the backend is complete.

Mock mode rules:

- Mock payloads must exactly match the canonical schemas.
- Keep mock data in a dedicated `mocks/` or `lib/mock-api.ts` location.
- Select mock mode only through `NEXT_PUBLIC_USE_MOCK_API=true` or an explicit development adapter.
- Never scatter hardcoded diagnosis objects across components.
- The final demo must set mock mode to false.

Mocks should cover all three fixtures and produce different categories and root-cause IDs.

### 11.17 Person 2 Definition of Done

Person 2's module is complete when:

- The frontend starts independently.
- It can run against schema-accurate mocks.
- It can switch to the real backend by changing environment configuration only.
- All four canonical endpoints are consumed correctly.
- All three fixture traces appear in the selector.
- The raw JSON view renders complete trace payloads.
- The TraceMind graph renders nodes and directed edges.
- The root-cause node is visually obvious.
- Evidence and critical paths are distinguishable.
- The diagnosis card shows every required field.
- The regression button displays the returned JSON artifact.
- Loading and API failures do not crash the page.
- No diagnosis or causal logic is duplicated in the frontend.
- `npm run build` and TypeScript checks pass.

---

## 12. Backend Implementation Conventions

Recommended backend structure:

```text
backend/
├── app/
│   ├── main.py
│   ├── models.py
│   ├── fixtures.py
│   ├── graph_builder.py
│   ├── analyzer.py
│   ├── diagnoser.py
│   ├── regression.py
│   └── routes.py
├── tests/
├── requirements.txt
└── .env.example
```

Conventions:

- Type all public functions.
- Use Pydantic models at API boundaries.
- Keep fixture creation separate from analysis logic.
- Keep deterministic analysis separate from the LLM call.
- Validate every LLM response.
- Return stable JSON shapes.
- Use fixture IDs as cache keys.
- Never expose API keys to the frontend.
- Keep LLM prompts on the backend.

Suggested environment variables:

```bash
ANTHROPIC_API_KEY=
LLM_MODEL=
FRONTEND_ORIGIN=http://localhost:3000
USE_CACHED_DIAGNOSES=true
```

The provider may be changed, but the response contract must not change.

---

## 13. Frontend Coding Conventions

- Use TypeScript strict mode.
- Prefer small functional components.
- Keep API logic in one module.
- Keep graph transformation in pure helpers.
- Avoid `any`; use `unknown` and narrow it.
- Use semantic names based on domain terms: trace, diagnosis, evidence, root cause, critical path.
- Do not rename backend fields in the transport layer.
- Components may receive camelCase view models only when a deliberate mapping layer exists.
- Do not calculate a new confidence score in the frontend.
- Do not infer a different root cause in the frontend.
- Avoid unnecessary animations that could fail during the live demo.
- Make the primary demo flow accessible without page navigation.

---

## 14. API and Integration Conventions

### Contract Freeze

Before parallel implementation, both contributors must agree on:

- Route names.
- Fixture IDs.
- Response schemas.
- Graph serialization.
- Error response behavior.
- Local ports.

Canonical local ports:

```text
Frontend: http://localhost:3000
Backend:  http://localhost:8000
```

### CORS

FastAPI must allow the frontend origin during local development:

```text
http://localhost:3000
```

Do not solve CORS by disabling browser security or embedding backend calls in random Next.js server routes unless both contributors intentionally adopt that architecture.

### Error Shape

Prefer FastAPI's standard form:

```json
{
  "detail": "Trace not found"
}
```

The frontend should also handle non-JSON errors.

### Stable Identifiers

The following values are stable contracts:

- Trace IDs.
- Node IDs within fixtures.
- Failure taxonomy strings.
- Suggested-fix type strings.
- Route paths.

Changing display names is safe. Changing IDs is breaking.

---

## 15. Testing Strategy

### Backend Tests

At minimum, verify for every fixture:

- Graph contains all fixture nodes.
- Every `reads_from` reference becomes an edge.
- Root-cause ID exists.
- Evidence IDs exist.
- Evidence is structurally connected.
- Expected failure category is returned.
- Root cause is upstream of the visible failure.
- Regression artifact includes the correct trace and root-cause category.

The key acceptance assertion is not merely “a diagnosis exists.” It is that the selected root cause is earlier than the visible failure.

### Frontend Tests

At minimum, verify:

- Trace list renders.
- Selecting a trace requests the correct ID.
- Raw JSON tab renders the trace.
- Diagnose calls the correct endpoint.
- Root-cause visual state is assigned to the correct node.
- Diagnosis fields render.
- Regression button calls the correct endpoint.
- Error messages render for failed requests.

### Manual End-to-End Test

Run this exact sequence:

1. Start backend on port 8000.
2. Start frontend on port 3000 with mock mode disabled.
3. Load the retrieval fixture.
4. Show raw JSON.
5. Click or switch to diagnose.
6. Confirm the stale retrieval node is red and upstream.
7. Confirm category is `Retrieval`.
8. Confirm evidence path is highlighted.
9. Generate regression artifact.
10. Repeat briefly for Tool and Coordination fixtures.

---

## 16. Demo Contract

The UI must support this presentation without code changes:

1. Open the retrieval-failure trace in Raw Trace view.
2. Explain that raw logs show events but do not reveal the true causal break.
3. Switch to TraceMind view.
4. Point to the red stale-retrieval node several steps before the bad final answer.
5. Explain that all downstream reasoning was correct over the wrong input.
6. Show category, confidence, evidence, explanation, and concrete fix.
7. Generate the regression-test artifact.
8. Close with: “Every other tool shows you what happened. TraceMind shows you why.”

Use cached diagnosis responses during rehearsal and the final demo when live LLM latency or quota creates risk.

---

## 17. Git and Collaboration Rules

Recommended ownership branches:

```text
person-1/backend-engine
person-2/frontend-ui
```

Integration rules:

- Commit schema changes separately and clearly.
- Do not edit the other contributor's owned module without communication.
- Merge the shared contract before implementation branches diverge.
- Keep mock payloads synchronized with backend example responses.
- Resolve route/schema disagreement in this file first, then update code.
- Avoid large formatting-only commits during the hackathon.
- Do not commit `.env.local`, API keys, generated caches, or dependency directories.

Suggested commit prefixes:

```text
feat(frontend):
feat(backend):
fix(api):
fix(graph):
test(frontend):
test(backend):
docs:
```

---

## 18. Integration Checklist

Before declaring the project integrated, confirm:

- [ ] Backend is reachable from the browser.
- [ ] CORS accepts `http://localhost:3000`.
- [ ] `GET /traces` returns three summaries.
- [ ] `GET /traces/{id}` matches frontend `Trace` type.
- [ ] `POST /traces/{id}/diagnose` matches `FullDiagnosisResponse`.
- [ ] Graph contains `nodes` and `edges` arrays.
- [ ] Node IDs in diagnosis exist in the graph.
- [ ] Root cause is highlighted correctly.
- [ ] Evidence path is highlighted correctly.
- [ ] `critical_path` is an ordered string array.
- [ ] Confidence is represented from 0 to 1, not 0 to 100.
- [ ] Regression endpoint matches `RegressionTest`.
- [ ] All three categories differ as expected.
- [ ] Mock mode is disabled for the live demo.
- [ ] No secret is present in frontend code or git history.
- [ ] Both applications build without errors.
- [ ] The complete demo has been rehearsed from a clean start.

---

## 19. Known Integration Risks

### Route drift

Risk: one module uses `/trace/{id}` or `/diagnose` while the other uses `/traces/{id}/diagnose`.

Resolution: `/traces` plural and the four routes in Section 9 are canonical.

### Graph-shape drift

Risk: backend returns NetworkX node-link format while frontend expects custom `nodes` and `edges`.

Resolution: use the custom serialization contract in Section 10 or update both sides and this file together.

### Confidence-scale mismatch

Risk: backend returns `87` while frontend expects `0.87`.

Resolution: API confidence is always `0.0` to `1.0`; frontend converts it to a percentage.

### Node-type mismatch

Risk: fixtures introduce `retrieval` although the enum does not contain it.

Resolution: represent retrieval using `tool_call` or `observation` plus metadata.

### Evidence mismatch

Risk: LLM returns invented node IDs.

Resolution: backend validates IDs and connectivity before responding.

### Frontend duplication of diagnosis logic

Risk: UI highlights nodes based on its own anomaly assumptions and disagrees with backend.

Resolution: frontend uses backend diagnosis, evidence IDs, anomalies, and critical path only.

### Mock/real API divergence

Risk: frontend works with mocks but fails against FastAPI.

Resolution: mocks must be copied from canonical response examples and integration must happen early.

### Demo dependence on live LLM

Risk: latency, quota, or network failure ruins the demo.

Resolution: cache validated responses per fixture while retaining the real diagnosis path.

---

## 20. Scope Guard

Before adding a feature, ask whether it directly improves the five-minute demo of causal diagnosis. If not, defer it.

Explicitly deferred:

- Live agent instrumentation.
- OpenTelemetry ingestion.
- Historical baseline learning.
- Similar-failure vector retrieval.
- Counterfactual replay.
- Automatic self-healing.
- Predictive failure prevention.
- Multi-model routing.
- Enterprise authentication.
- Cloud deployment.
- Real CI execution of regression artifacts.

These may be presented as future work, but they must not block the MVP.

---

## 21. Final Acceptance Criteria

TraceMind is done for the hackathon when:

- All three fixtures load.
- Each fixture produces its expected distinct failure category.
- Each root cause is upstream of the visible failure.
- Structural analysis is deterministic.
- The LLM is called once per uncached diagnosis.
- LLM evidence is validated against the graph.
- The graph highlights root cause and evidence clearly.
- The diagnosis card provides a concrete fix.
- The regression artifact is generated and displayed.
- Raw JSON versus TraceMind value is obvious within five seconds.
- The full demo works from a clean local startup without manual data editing.

When trade-offs arise, choose deterministic integration and demo reliability over additional sophistication.
