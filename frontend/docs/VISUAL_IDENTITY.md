# ICHNOUS VISUAL IDENTITY

## Positioning
Ichnous is an AI Investigation Workspace that reconstructs execution trails, uncovers the true root cause of failures, and guides developers from evidence to resolution.

This document defines the personality of Ichnous. It translates the Product Constitution into actionable identity tokens. The visual goal is: *"If Linear designed an AI investigation platform."*

## 1. Product Personality
Ichnous should feel like a calm expert sitting beside the developer. It should never overwhelm. It should never dramatize. It should quietly guide the user toward understanding. 

Confidence comes from clarity—not complexity.

## 2. Color System (Warm Light)
We reject the standard dark-mode monitoring console. Ichnous uses a warm, intelligent light interface.

**Backgrounds (The Canvas)**
- `--bg-base`: `#F9F9F8` (Warm off-white, calm and premium)
- `--bg-surface`: `#FFFFFF` (Pure white for elevated panels and sections)
- `--bg-canvas`: `#F3F3F1` (Deeper tone for the Canvas)

**Borders (Structure)**
- `--border-subtle`: `#E5E5E5` (Internal dividers)
- `--border-strong`: `#171717` (2px stark black border)
- `--border-focus`: `#171717` (Thick black focus ring)

**Semantic Status Colors (The Evidence)**
- `--color-evidence` (Amber): `#F59E0B`
- `--color-root-cause` (Red): `#B91C1C` (Deep, premium red)
- `--color-recommendation` (Blue): `#1D4ED8` (High-contrast blue)
- `--color-safeguard` (Green): `#16A34A`

## 3. Typography
- **Display & Headings:** `Space Grotesk` (Confident, slightly mechanical).
- **Body & UI:** `Inter` (Functional, invisible).
- **Data & Evidence:** `JetBrains Mono` or `Geist Mono` (Strictly for raw data and node IDs).

## 4. Neo-Brutalist Confidence
**Neo Brutalism is used for confidence, not decoration.**
It signals irrefutable facts.
- **Borders:** Panels and primary buttons use a harsh `2px solid var(--border-strong)`.
- **Border Radius:** Unapologetically sharp. `0px` for main panels, `2px` for inner elements.
- **Shadows (The Offset):** Flat UI by default. The *Shadow-Truth* (`4px 4px 0px 0px #171717`) is reserved exclusively for the Root Cause node and primary actions to give them undeniable physical weight.

## 5. Layout Behavior
The application uses a persistent three-column layout.
- **Sidebar:** Fixed width (240–280px).
- **Investigation Canvas:** Fluid, occupies all remaining space.
- **Investigation Summary:** Fixed width (360–420px).
- **Execution Timeline:** Docked to the bottom and collapsible.

## 6. What the User Should Notice
The interface should intentionally direct attention in this exact order:
1. **Immediately after opening:** The Investigation Canvas.
2. **After selecting a Case:** The reconstruction animation.
3. **After investigation:** The Root Cause.
4. **After reading:** The Recommendation.

## 7. Flagship Components

### Investigation Overlay
The Investigation Overlay appears immediately after a Case is selected.
- **Purpose:** Communicate that structural analysis is occurring before any AI explanation.
- **Behavior:** It NEVER blocks the graph. It floats above it.
- **Contents:** Current Investigation Stage, Progress Indicator (`██████░░░░`), Current Node, Elapsed Time.
- **Resolution:** The graph continues reconstructing underneath. The overlay disappears once the Root Cause is revealed.

### Investigation Summary
Not one card, but four distinctly stacked Linear-style sections separated by stark borders:
────────────────────
Root Cause
────────────────────
Evidence
────────────────────
Recommendation
────────────────────
Safeguard
────────────────────

### Semantic Graph Tokens
Nodes possess both **Types** and **States**.
- **Types (Background Tints):** Planning (`bg-purple-50`), Retrieval (`bg-blue-50`), Tool Call (`bg-teal-50`), Reasoning (`bg-gray-100`).
- **States (Behavior):**
  - *Idle:* Muted, 1px subtle border.
  - *Analyzing:* Gently pulsing border.
  - *Evidence:* Bright `bg-amber-100`, 2px solid Amber border.
  - *Root Cause:* Bright `bg-red-100`, 2px solid Red border, pulsing ring, Shadow-Truth offset.
  - *Focused:* 2px Black focus ring.
  - *Dimmed:* Opacity reduced to 30% to hide irrelevant branches.

## 8. Animation Timeline
Every engineer must build this exact cinematic sequence, divided strictly into two phases to respect backend constraints:

**Phase 1: Investigation Phase (API Request Active)**
- Begins immediately after a Case is selected.
- The **Investigation Overlay** appears and communicates progress (e.g., `Investigating... ██████░░░░ 62%`) without inventing data.
- The frontend sends the `POST /traces/{id}/diagnose` request.

**Phase 2: Reveal Phase (API Request Resolved)**
Begins only after the backend response is received. The frontend animates the verified backend output:
- **0ms:** Graph reconstruction begins (nodes illuminate based on backend truth).
- **300ms:** Evidence is highlighted in Amber.
- **550ms:** Camera movement centers the graph on the failure origin.
- **800ms:** Root Cause pulses in Red.
- **1050ms:** Summary sections reveal (staggered).
- **1300ms:** Timeline syncs to the Root Cause timestamp.
- **1550ms:** Overlay disappears.
- **1850ms:** Replay becomes available.

## 9. Empty States
Every component must clearly communicate intent when empty:
- **Investigation Summary:** *"Select a Case to begin."*
- **Execution Timeline:** *"No execution available."*
- **Investigation Canvas:** *"AI failures leave clues."*
- **Cases Sidebar:** *"No investigations available."*
