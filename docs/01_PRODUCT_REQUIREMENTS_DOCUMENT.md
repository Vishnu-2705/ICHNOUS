# Product Requirements Document (PRD) — TraceMind / ICHNOUS

**Product Title:** TraceMind / ICHNOUS — The Causal Debugger for Autonomous AI Systems  
**Document Version:** 1.0.0 (Production Release)  
**Status:** Approved & Implemented Single Source of Truth  
**Target Platform:** Desktop Web Application (FastAPI + Next.js 16)

---

## 1. Executive Summary

### 1.1 Product Vision
TraceMind (branded as **ICHNOUS**) is an enterprise-grade AI Investigation Workspace and Causal Reliability Platform designed to reconstruct execution trails, uncover the true root causes of autonomous AI agent failures, and guide software engineers from anomalous telemetry to verified, 1-line code fixes.

### 1.2 Core Problem Statement
Autonomous AI multi-agent systems (built with frameworks like LangChain, LangGraph, CrewAI, AutoGen, or custom OTel instruments) fail in non-deterministic, complex ways—such as infinite delegation loops, stale vector database retrievals, tool response rate-limit truncations, and subtle attribute typos (e.g., `self.memories` vs `self.memory`).

Traditional observability tools (e.g., Datadog, LangSmith, Arize Phoenix) show **what** happened (logs, spans, latency graphs) but fail to explain **why** it happened or **how** to fix it. Developers waste hours manually inspecting nested trace spans and raw JSON logs to find single-line bugs.

### 1.3 Product Mission & Pitch
> *"Every other observability tool shows what happened. TraceMind shows why—and gives the fix."*

TraceMind transforms complex agent execution telemetries into an interactive 6-stage progressive disclosure workflow:
1. Reconstructs execution DAGs (Directed Acyclic Graphs).
2. Performs backward causal walks and anomaly detection.
3. Ranks root-cause failure candidates.
4. Synthesizes 3-part developer-friendly LLM explanations (Root Cause, Technical Breakdown, Recommended Fix).
5. Generates concrete 1-line `git-diff` patch proposals.
6. Executes closed-loop sandbox verification to prove patch correctness before deployment.

### 1.4 Business Objectives & Key Success Metrics
- **Mean Time to Diagnosis (MTTD):** Reduce agent failure diagnosis time from 45+ minutes to **< 8 seconds**.
- **First-Time User Understanding:** A developer must understand **what failed** in **< 3 seconds**, identify **root cause** in **< 8 seconds**, and review **suggested patch** in **< 15 seconds**.
- **Automated Verification:** 100% closed-loop patch verification in isolated PyTorch/Python sandboxes.
- **Cache Hit Latency:** Re-analyzing identical source code files in **< 5ms** using SHA-256 content hashing.

---

## 2. Target Users & Personas

### 2.1 User Personas

| Persona | Role | Key Needs & Objectives | Pain Points |
|---|---|---|---|
| **Alex — AI Engineer** | Builds LangGraph / CrewAI multi-agent pipelines | Needs rapid root-cause isolation for agent crashes & hallucinated tool outputs | Nested span traces take hours to read; non-deterministic failures are hard to reproduce |
| **Priya — Tech Lead / Architect** | Oversees AI reliability & production deployments | Requires automated regression testing artifacts & closed-loop patch verification | Unverified patches break downstream agent workflows; lack of CI regression suites |
| **Sam — DevOps / Site Reliability Eng.** | Monitors production agent runtime services | Demands instant OpenTelemetry OTLP ingestion, webhooks, & Neo4j graph exports | Obscure agent exceptions trigger midnight alerts without clear remediation steps |

### 2.2 User Roles & Access Control
- **Viewer / Analyst:** Inspects investigation cases, graph execution flows, root cause cards, and diagnostic explanations.
- **Developer / Operator:** Uploads custom Python agent scripts, triggers live interactive scenario streams, runs closed-loop sandbox verifications, and exports JSON regression artifacts.
- **Administrator:** Configures global API integrations (OpenAI, Anthropic, NVIDIA NIM, Arize Phoenix, Neo4j) and manages backend session cleanup TTLs.

---

## 3. Comprehensive Feature Catalog

### 3.1 Source Code & Telemetry Ingestion
- **Python Source Upload (`.py`):** Drag-and-drop or file selector uploading. Supports LangGraph, CrewAI, AutoGen, OpenAI SDK, Anthropic SDK, and custom agents.
- **Framework Auto-Detection:** Automatically inspects Python AST and import headers to categorize the agent framework.
- **OpenTelemetry / OTLP Integration (`agent365`):** Ingests standardized OTLP spans, Arize Phoenix traces, and webhook payloads into NetworkX DiGraph models.
- **SHA-256 Upload Acceleration Cache:** In-memory code hash lookup (`_UPLOAD_CACHE`) returning analysis results in **< 5ms** for previously analyzed source files.

### 3.2 Dynamic Execution Graph Engine
- **NetworkX DiGraph Serialization:** Serializes trace events into nodes and directed dependency edges matching the canonical schema.
- **Dagre Automatic Graph Layout:** Computes hierarchy coordinates (`x, y`) for clean top-to-bottom DAG visualization.
- **Anomalous Node Highlighting:** Distinguishes nodes visually into `root_cause` (glowing red), `evidence` (amber), `critical_path` (yellow), and `normal` (neutral slate).
- **Interactive Replay & Scrubbing:** Step-by-step interactive timeline scrubbing to replay agent execution step-by-step.

### 3.3 Root Cause & Anomaly Intelligence
- **Statistical Anomaly Detection:** Identifies execution exceptions, rate-limit truncations, infinite loop cycles, and telemetry metric deviations.
- **Backward Causal Walk:** Algorithmically traverses dependency edges backward from failure sinks to locate origin root-cause nodes.
- **PyTorch HGT GNN Intelligence Engine:** Heterogeneous Graph Transformer (HGT) neural network model predicting failure category, regression risk, and GNNExplainer subgraph masks.

### 3.4 Grounded LLM Diagnosis & 3-Part Developer Explanations
- **Strict Evidence Grounding:** Constrains LLM outputs strictly to observed telemetry without hallucinating arbitrary character thresholds.
- **3-Part Developer Breakdown:**
  1. 🔍 **Root Cause:** Exact exception type, file, line number, and attribute.
  2. 💡 **Technical Analysis:** Deep architectural breakdown of why the bug occurred.
  3. 🛠️ **Recommended Fix:** Step-by-step developer remediation guidance.
- **Concrete Code Patch Diff:** Formatted green addition / red deletion 1-line `git-diff` viewer with one-click copy.

### 3.5 Closed-Loop Sandbox Patch Verification
- **Isolated Code Execution:** Runs patched code in a temporary Python sandbox process.
- **Test Harness Verification:** Validates whether the applied `git-diff` eliminates runtime exceptions.
- **Confidence Boosting:** Increases diagnosis confidence by +15% upon successful sandbox patch verification.

---

## 4. Functional & Non-Functional Requirements

### 4.1 Functional Requirements Matrix

| ID | Requirement Category | Description | Priority | State |
|---|---|---|---|---|
| **FR-1** | Upload & Ingestion | Ingest `.py` Python files up to 5MB and extract AST/spans | Critical | Implemented |
| **FR-2** | Graph Processing | Build NetworkX DiGraph and serialize nodes/edges for React Flow | Critical | Implemented |
| **FR-3** | Anomaly & Causal Analysis | Execute backward walk, anomaly detection, and divergence ranking | Critical | Implemented |
| **FR-4** | LLM Explanation | Synthesize structured 3-part developer explanation & git diff | Critical | Implemented |
| **FR-5** | Sandbox Verifier | Execute closed-loop patch verification in subprocess sandbox | High | Implemented |
| **FR-6** | View Mode Toggle | Toggle between **Guided Workflow Mode** and **Full Dashboard Mode** | High | Implemented |
| **FR-7** | Regression Artifact | Generate and export JSON regression test reproduction payloads | Medium | Implemented |
| **FR-8** | Live Scenario Stream | Stream live interactive scenario traces via WebSocket (`/ws/sessions/{id}`) | Medium | Implemented |

### 4.2 Non-Functional Requirements Matrix

| ID | Metric / Area | Target Benchmark | Actual Measured Performance |
|---|---|---|---|
| **NFR-1** | Upload Analysis Latency (Uncached) | < 3.0s | **1.2s - 2.5s** |
| **NFR-2** | Upload Analysis Latency (Cached) | < 10ms | **< 4ms** (SHA-256 hit) |
| **NFR-3** | UI Render Speed | < 100ms | **35ms** (Next.js SSR) |
| **NFR-4** | Backend Unit Test Coverage | 100% core algorithms | **166/166 Pytest passed** |
| **NFR-5** | Reliability & Safety | 0 unhandled process crashes | **100% sandboxed subprocess isolation** |
