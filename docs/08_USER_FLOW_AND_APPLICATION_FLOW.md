# User Flow & Application Flow Documentation — TraceMind / ICHNOUS

**Product Title:** TraceMind / ICHNOUS — Application Workflow & User Journey Blueprint  
**Document Version:** 1.0.0 (Production Release)  
**Status:** Approved Technical Single Source of Truth

---

## 1. End-to-End User Flow: Upload-to-Verified-Fix

```mermaid
flowchart TD
    A[Start: User Opens http://localhost:3000] --> B{Choose Entry Point}
    
    B -->|Option 1: Upload Python Agent File| C[Stage 1: Drag & Drop .py File]
    B -->|Option 2: Select Pre-built Case| D[Click Sidebar Scenario Case]
    B -->|Option 3: Trigger Live Scenario| E[Click Header Trigger Scenario Dropdown]

    C --> F[Frontend reads file.text and POSTs /upload/analyze-code]
    D --> G[Fetch GET /traces/id or GET /sessions/id]
    E --> H[POST /sessions/demo/scenario & connect WebSocket]

    F --> I[Stage 2: Automatic Graph Construction]
    G --> I
    H --> I

    I --> J[Stage 3: Highlight Root Cause Node & Divergence Gauge]
    J --> K[Stage 4: Synthesize 3-Part Developer LLM Explanation]
    K --> L[Stage 5: Click 'Run Sandbox Verification']
    L --> M[Sandbox executes git-diff patch test]
    
    M -->|Verification Passed| N[Stage 6: Verified Fix Confirmed + Download JSON Artifact]
    M -->|Verification Failed| O[Display Sandbox Error Log & Adjust Patch]
```

---

## 2. Comprehensive Workflow Descriptions

### 2.1 File Upload Workflow (Stage 1 -> Stage 6)
1. **User Action:** User drags `failing_agent.py` into the Stage 1 dropzone or modal.
2. **Frontend Processing:** Reads the file text asynchronously, detects framework imports (`custom`), and posts `Content-Type: application/json` to `POST /upload/analyze-code`.
3. **Backend Processing:** Checks SHA-256 cache. On hit (<5ms), returns cached session. On miss, executes code in sandboxed process, parses exception, builds NetworkX graph, computes backward walk, calls LLM diagnoser, and runs patch verifier.
4. **UI State Transition:** Automatically advances stepper from `Stage 1: Upload & Ingest` -> `Stage 2: Graph Build` -> `Stage 3: Root Cause` -> `Stage 4: AI Diagnosis`.
5. **Verification & Completion:** User clicks `Run Sandbox Verification →`. Verification terminal streams execution status. Upon success, Stage 6 displays a green "VERIFIED FIX CONFIRMED" banner.

---

## 3. Navigation Hierarchy & Route Map

| Client Route | View Mode | Key Components | Trigger / Condition |
|---|---|---|---|
| `/` | Guided Workflow Mode | `WorkflowStepper`, `GuidedWorkflowView` | Default app landing |
| `/` (Toggle) | Full Dashboard Mode | `Header`, `CasesSidebar`, `GraphCanvas`, `InvestigationSummary`, `ExecutionTimeline` | Clicked "Full Dashboard Mode" toggle |
