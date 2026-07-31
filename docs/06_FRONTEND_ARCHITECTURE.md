# Frontend Architecture Documentation — TraceMind / ICHNOUS

**Product Title:** TraceMind / ICHNOUS — Frontend Architecture & Component Blueprint  
**Document Version:** 1.0.0 (Production Release)  
**Status:** Approved Technical Single Source of Truth  
**Framework:** Next.js 16 (App Router) / React 19 / TypeScript 5 / Tailwind CSS

---

## 1. Directory Structure & App Architecture

```
frontend/src/
├── app/
│   ├── layout.tsx             # Root layout, fonts (Space Grotesk, Inter, JetBrains Mono), Providers
│   ├── page.tsx               # Main application container, stage router, view mode toggle
│   └── globals.css            # Design tokens, CSS variables, custom scrollbars, animations
├── components/
│   ├── header.tsx             # Top bar: Branding, View Mode Toggle, Live Demo trigger, Upload button
│   ├── providers.tsx          # React Query (QueryClientProvider) & RevealContext providers
│   ├── source-code-upload-modal.tsx # Drag-and-drop Python upload modal with sandbox status
│   ├── diagnosis-card.tsx     # Structured 3-part diagnosis card (Root Cause, Analysis, Fix)
│   ├── suggested-fix.tsx      # Formatted 1-line git-diff code patch viewer
│   ├── graph/
│   │   ├── GraphCanvas.tsx    # React Flow (@xyflow/react) interactive DAG renderer
│   │   └── CustomGraphNode.tsx# Custom node component (glowing root cause, evidence badges)
│   ├── sidebar/
│   │   ├── cases-sidebar.tsx  # Left case selector with search, filters, and auto-selection
│   │   └── trace-selector.tsx # Fixture scenario selector dropdown
│   ├── summary/
│   │   └── InvestigationSummary.tsx # Right panel 30% investigation summary card
│   ├── timeline/
│   │   └── ExecutionTimeline.tsx    # Chronological step timeline with scrubber
│   ├── workflow/
│   │   ├── workflow-stepper.tsx     # Horizontal 6-stage progressive disclosure stepper
│   │   └── guided-workflow-view.tsx # Main guided workflow stage manager & card renderer
├── lib/
│   ├── api.ts                 # Type-safe API client for REST endpoints & sandbox upload
│   ├── graphMapper.ts         # Maps NetworkX SerializedGraph / Trace.nodes to React Flow nodes/edges using Dagre layout
│   └── mock-api.ts            # Fallback mock API provider for independent UI testing
└── types/
    └── tracemind.ts           # Shared TypeScript interfaces matching backend Pydantic models
```

---

## 2. Core State Management & Data Fetching

### 2.1 State Architecture
1. **View Mode State (`viewMode`):** `guided` (Guided 6-Stage Workflow Mode) vs `dashboard` (Full 3-Column Workspace Mode).
2. **Workflow Stage State (`currentStage`):** `upload` -> `graph` -> `root_cause` -> `diagnosis` -> `verify` -> `verified`.
3. **Selected Case State (`selectedCaseId`):** UUID or fixture ID of currently selected investigation session.
4. **TanStack React Query Cache:**
   - Query Key `["cases"]`: Fetches `/sessions` + `/traces` listing.
   - Query Key `["trace", id]`: Fetches full trace payload with `staleTime: 600,000` (10 minutes).
   - Query Key `["diagnosis", id]`: Fetches diagnosis response with `staleTime: 600,000` (10 minutes).

---

## 3. Dynamic Graph Rendering Engine (`lib/graphMapper.ts` & `GraphCanvas.tsx`)

### 3.1 Dagre Automatic Layout Algorithm
The graph mapper converts backend `SerializedGraph` or `Trace.nodes` into `@xyflow/react` node objects:
```typescript
import dagre from "dagre";

const NODE_WIDTH = 230;
const NODE_HEIGHT = 120;

export function mapTraceToReactFlow(trace: Trace, diagnosis?: FullDiagnosisResponse | null) {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setGraph({ rankdir: "TB", nodesep: 40, ranksep: 60 });
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  // Add nodes and edges to Dagre graph...
  dagre.layout(dagreGraph);

  // Assign x, y coordinates to React Flow nodes...
}
```

---

## 4. Progressive Disclosure 6-Stage Workflow

```
+---------------------------------------------------------------------------------------+
| 1. Upload & Ingest  -->  2. Graph Build  -->  3. Root Cause  -->  4. AI Diagnosis  |
|                                                                         |             |
| 6. Verified Dashboard  <--  5. Patch Verify  <--------------------------+             |
+---------------------------------------------------------------------------------------+
```

1. **Stage 1 (Upload & Ingest):** Drag-and-drop `.py` file upload area with framework cards.
2. **Stage 2 (Graph Build):** Interactive React Flow execution DAG with Dagre auto-layout.
3. **Stage 3 (Root Cause):** Isolated root cause candidate card with confidence score & divergence metrics.
4. **Stage 4 (AI Diagnosis):** Structured 3-part developer explanation (Root Cause, Analysis, Recommended Fix) + git diff viewer.
5. **Stage 5 (Patch Verify):** Live terminal execution streaming line-by-line sandbox verification.
6. **Stage 6 (Verified Dashboard):** Green "VERIFIED FIX CONFIRMED" banner, complete graph, patch, download button, and collapsible GNN Intelligence details.
