# Complete API Reference — TraceMind / ICHNOUS

**Product Title:** TraceMind / ICHNOUS — REST & WebSocket Endpoint Specifications  
**Document Version:** 1.0.0 (Production Release)  
**Status:** Approved Technical Single Source of Truth  
**Base URL:** `http://localhost:8000`

---

## 1. System & Health Endpoints

### 1.1 Root Endpoint
- **Route:** `GET /`
- **Description:** Landing page rendering HTML API index and interactive documentation links.
- **Response:** `200 OK` (`text/html`)

### 1.2 Health Check & Metrics
- **Route:** `GET /health`
- **Description:** System health check returning uptime, WebSocket connection count, and session metrics.
- **Response:** `200 OK` (`application/json`)
```json
{
  "status": "healthy",
  "service": "TraceMind Backend",
  "version": "0.2.0",
  "llm_configured": true,
  "uptime_seconds": 342.15,
  "websocket_connections": 1,
  "metrics": {
    "total_sessions": 12,
    "active_sessions": 0,
    "completed_sessions": 11,
    "failed_sessions": 1
  }
}
```

---

## 2. Traces Catalog Endpoints (`routes/traces.py`)

### 2.1 List Hardcoded Traces Catalog
- **Route:** `GET /traces`
- **Description:** Returns summary catalog of built-in trace scenario fixtures (`retrieval_failure`, `tool_failure`, `coordination_failure`).
- **Response:** `200 OK` (`application/json`)
```json
[
  {
    "id": "retrieval_failure",
    "name": "Retrieval Failure Scenario",
    "description": "Agent retrieves stale 2023 refund policy document",
    "failure_category": "Retrieval"
  }
]
```

### 2.2 Get Specific Trace Details
- **Route:** `GET /traces/{trace_id}`
- **Description:** Returns full trace detail object including raw telemetry events.
- **Response:** `200 OK` (`application/json`) | `404 Not Found`

### 2.3 Diagnose Static Trace
- **Route:** `GET /traces/{trace_id}/diagnose`
- **Description:** Runs causal graph analysis, anomaly detection, backward walk, and LLM diagnosis on static trace fixture.
- **Response:** `200 OK` (`application/json`) -> Returns `FullDiagnosisResponse`.

### 2.4 Run GNN Neural Prediction
- **Route:** `POST /traces/{trace_id}/gnn-predict`
- **Description:** Executes PyTorch HGT GNN forward pass, memory bank retrieval, and GNNExplainer subgraph masks.
- **Response:** `200 OK` (`application/json`) -> Returns `GNNPredictionResponse`.

---

## 3. Live Sessions Endpoints (`routes/sessions.py`)

### 3.1 List Active & Completed Sessions
- **Route:** `GET /sessions`
- **Description:** Returns list of lightweight `SessionSummary` items.
- **Response:** `200 OK` (`application/json`)

### 3.2 Create New Live Session
- **Route:** `POST /sessions`
- **Description:** Initializes a new live agent session.
- **Request Body:** `StartSessionRequest` (`name`, `description`, `tags`)
- **Response:** `201 Created` (`application/json`) -> `{ "session_id": "...", "status": "created" }`

### 3.3 Emit Trace Event to Session
- **Route:** `POST /sessions/{session_id}/events`
- **Description:** Appends a new `TraceEvent` to an active session and broadcasts to WebSocket clients.
- **Request Body:** `TraceEvent` payload.
- **Response:** `200 OK` (`application/json`)

### 3.4 Finish & Diagnose Live Session
- **Route:** `POST /sessions/{session_id}/finish`
- **Description:** Transitions session to `COMPLETED` and triggers causal diagnosis pipeline.
- **Request Body:** `FinishSessionRequest` (`trigger_diagnosis: true`)
- **Response:** `200 OK` (`application/json`) -> Returns `FullDiagnosisResponse`.

### 3.5 Live Demo Scenario Stream
- **Route:** `POST /sessions/demo/{scenario}`
- **Description:** Launches background task that streams pre-recorded live scenario events (`retrieval_failure`, `tool_failure`, `coordination_failure`) over WebSocket line-by-line.
- **Response:** `200 OK` (`application/json`)

---

## 4. Source Code Upload & Sandbox Analysis (`routes/upload.py`)

### 4.1 Upload & Analyze Agent Source Code
- **Route:** `POST /upload/analyze-code`
- **Description:** Accepts Python source code text, executes it in a sandboxed process, builds causal execution DAG, runs diagnosis, executes closed-loop patch verification, and returns results. Includes SHA-256 caching (< 5ms turnaround).
- **Request Body:** `AnalyzeCodeRequest`
```json
{
  "code_text": "class Agent: ...",
  "framework": "custom",
  "session_name": "uploaded_agent.py"
}
```
- **Response:** `200 OK` (`application/json`)
```json
{
  "session_id": "7dafb28f-4adb-4b10-82ee-3762146d983c",
  "framework": "custom",
  "raw_code_length": 266,
  "status": "completed",
  "cached": true,
  "diagnosis": {
    "diagnosis": {
      "failure_category": "Memory",
      "confidence": 1.0,
      "root_cause_node_id": "evt_c2b0e338",
      "explanation": "🔍 Root Cause: AttributeError...\n\n💡 Technical Analysis: ...\n\n🛠️ Recommended Fix: ...",
      "suggested_fix": {
        "type": "prompt_patch",
        "target": "failing_agent.py",
        "diff": "--- a/failing_agent.py\n+++ b/failing_agent.py\n@@ -5,1 +5,1 @@\n-    return self.memories[-1]\n+    return self.memory[-1]"
      }
    }
  }
}
```

---

## 5. WebSocket Protocol Reference

### 5.1 Session Event Stream
- **Endpoint:** `WS /ws/sessions/{session_id}`
- **Description:** Bi-directional WebSocket stream broadcasting real-time trace events, graph delta nodes, and live diagnosis updates.
- **Event Message Frame:**
```json
{
  "event": "trace_event",
  "session_id": "7dafb28f-4adb-4b10-82ee-3762146d983c",
  "data": {
    "event_id": "evt_8d8d0b08",
    "event_type": "tool_call",
    "content": "execute_agent_routine()",
    "metadata": { "pipeline_stage": "execution" }
  }
}
```
