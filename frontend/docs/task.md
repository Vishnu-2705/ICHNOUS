# Ichnous Sprint Verification Checklist

- [x] **Backend Integration**
  - [x] GET /traces (Cases Sidebar)
  - [x] GET /traces/{id} (Trace DAG fetch)
  - [x] POST /traces/{id}/diagnose (Diagnosis Engine trigger)
  - [x] POST /traces/{id}/regression-test (Safeguard CTA hook)

- [x] **Reveal Sequence & Orchestration (2.4s State Machine)**
  - [x] Phase 1: Investigation Overlay (progress indicator `██████░░░░ 62%`)
  - [x] Phase 2: Reveal Animation (`dim` -> `evidence` -> `camera` -> `root_cause` -> `summary` -> `timeline` -> `complete`)
  - [x] Global Keyboard Shortcuts (`Shift + R` Replay, `Shift + S` Skip)

- [x] **Execution Graph Canvas**
  - [x] Neo-Brutalist styling (warm off-white `#F9F9F8` background, 2px borders, Space Grotesk 700 titles)
  - [x] Dagre auto-layout (`NODE_WIDTH = 230`, `NODE_HEIGHT = 120`)
  - [x] Custom Nodes (soft pastel tints: purple for plan, blue for retrieval, teal for tool, gray for reasoning, red for root cause)
  - [x] Node Dragging with live edge updates & automatic reset on Replay
  - [x] Interactive Node Inspector panel on click

- [x] **Cases Sidebar**
  - [x] Functional Tab Filtering (`All`, `Open`, `Resolved`) using `useMemo`
  - [x] Search filter
  - [x] Selection preservation & auto-select fallback
  - [x] Standardized 2-state status dots: 🟡 `Investigating` (Amber), 🟢 `Resolved` (Green)

- [x] **Investigation Summary Panel**
  - [x] 20px 2-stroke Lucide semantic section icons (Red Root Cause, Amber Evidence, Blue Recommendation, Green Safeguard)
  - [x] Custom 6px red Framer Motion Confidence progress bar
  - [x] Dark Linear-style code snippet
  - [x] Docked Replay Investigation & Skip Animation buttons

- [x] **Execution Timeline Drawer**
  - [x] Equal-width `120px` event columns
  - [x] Continuous centered backbone rail
  - [x] Human-readable concise action labels
