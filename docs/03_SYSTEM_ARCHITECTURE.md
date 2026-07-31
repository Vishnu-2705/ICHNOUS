# System Architecture Document — TraceMind / ICHNOUS

**Product Title:** TraceMind / ICHNOUS — High-Level & Detailed Architecture Blueprint  
**Document Version:** 1.0.0 (Production Release)  
**Status:** Approved Technical Single Source of Truth

---

## 1. High-Level System Architecture

TraceMind / ICHNOUS implements a multi-agent observability and causal intelligence architecture. The system converts linear trace events and telemetry spans into a NetworkX directed graph, runs deterministic graph analysis, passes evidence to an LLM diagnosis engine, and executes closed-loop verification.

```
                  +-----------------------------------+
                  |   Python SDK / Auto-Instrument    |
                  |  LangGraph | CrewAI | AutoGen     |
                  +-----------------------------------+
                                    |
                                    | OTLP / HTTP REST / WS
                                    v
+-----------------------------------------------------------------------+
|                       FASTAPI INGESTION ENGINE                        |
|                                                                       |
|  +-------------------+  +--------------------+  +------------------+  |
|  |  /upload/analyze  |  |  /sessions API     |  | WebSocket Hub    |  |
|  +-------------------+  +--------------------+  +------------------+  |
|                                   |                                   |
|                                   v                                   |
|                   SessionManager Storage (In-Memory)                  |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                    CAUSAL DIAGNOSIS PIPELINE                          |
|                                                                       |
|  1. Trace-to-Graph Conversion (NetworkX DiGraph)                       |
|  2. Anomaly Detection (Exceptions, Rate Limits, Truncation, Loops)     |
|  3. Critical Path Extraction (Longest path to failure sink)           |
|  4. Backward Causal Walk (Locates root cause candidate)              |
|  5. Divergence & Confidence Ranking                                    |
|  6. PyTorch HGT GNN Neural Forward Pass                               |
|  7. Memory Bank Vector Similarity Retrieval                           |
|  8. Grounded LLM Diagnosis (3-Part Developer Breakdown)               |
|  9. Closed-Loop Sandbox Patch Verifier                                |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                   ICHNOUS FRONTEND WORKSPACE (Next.js)                |
|                                                                       |
|  - 6-Stage Guided Workflow Stepper                                    |
|  - Full React Flow Execution Canvas (@xyflow/react)                   |
|  - 3-Part Developer Explanation & Patch Diff Cards                     |
|  - Sandbox Verification Terminal                                      |
+-----------------------------------------------------------------------+
```

---

## 2. Graph Processing Subsystem Architecture

### 2.1 NetworkX Graph Construction (`backend/graph/builder.py`)
Trace step events are mapped to graph nodes and directed edges:
- **Nodes (`SerializedGraphNode`):** Represent plan steps, tool executions, agent observations, thought processes, and final answers. Each node retains telemetry metadata (tokens, latency, error strings, truncation flags).
- **Edges (`SerializedGraphEdge`):** Directed causality edges representing workflow control flow (`step_N -> step_N+1`) and agent-to-agent delegation links.

### 2.2 Backward Causal Walk Algorithm (`backend/graph/analyzer.py`)
1. **Locate Failure Sink:** Finds terminal nodes with unhandled exceptions or error statuses.
2. **Extract Critical Path:** Computes the longest directed path from the root node to the failure sink using NetworkX path algorithms.
3. **Traverse Backward:** Walks upstream from the failure sink along critical path edges, evaluating divergence scores for each node:
   $$\text{Divergence} = w_1 \cdot \mathbb{I}_{\text{error}} + w_2 \cdot \Delta_{\text{latency}} + w_3 \cdot \mathbb{I}_{\text{truncated}} + w_4 \cdot \mathbb{I}_{\text{stale\_retrieval}}$$
4. **Select Candidate:** Selects the node with the highest divergence score as the root cause candidate.

---

## 3. PyTorch Heterogeneous Graph Transformer (HGT) GNN Architecture

### 3.1 Neural Tensor Network (`backend/gnn/`)
- **Node Encoder (`encoder.py`):** Converts heterogeneous node types (`plan`, `reasoning`, `tool_call`, `observation`, `final_answer`) into dense embedding vectors.
- **HGT Model (`pytorch_model.py`):** Runs PyTorch tensor forward passes over heterogeneous graphs to predict:
  - **Failure Category:** Multi-class classification probability distribution across failure taxonomy.
  - **Regression Risk Score:** Continuous risk metric between `0.0` and `1.0`.
  - **Confidence Score:** Prediction certainty weight.
- **Vector Memory Bank (`memory_bank.py`):** FAISS-like vector store maintaining historical trace motifs for similarity retrieval.
- **GNNExplainer (`explainer.py`):** Computes edge mask importance scores to highlight subgraphs responsible for predictions.

---

## 4. Closed-Loop Sandbox Verifier (`agent365/engine/verifier.py`)

### 4.1 Automated Patch Verification Loop
When the LLM synthesizer proposes a `git-diff` patch, the closed-loop verifier executes the following steps:
1. Spawns an isolated temporary directory.
2. Writes the original agent source code.
3. Applies the proposed `git-diff` patch via line manipulation.
4. Executes the patched Python file in a sandboxed subprocess.
5. If the process completes with `returncode == 0` and zero unhandled exceptions, `verified` is set to `True`, and diagnosis confidence is boosted by **+0.15**.
