# UI/UX Design Brief & Design System — TraceMind / ICHNOUS

**Product Title:** TraceMind / ICHNOUS — Design System & Visual Identity  
**Document Version:** 1.0.0 (Production Release)  
**Status:** Approved Design Single Source of Truth  
**Visual Personality:** 70% Linear, 20% Raycast, 10% Neo Brutalism

---

## 1. Design Philosophy & Core UX Values

ICHNOUS is designed around a single core directive: **Reduce cognitive effort during AI failure investigation.**

### 1.1 The Five Design Values
1. **Calm rather than noisy:** Minimal background distraction, dark slate surfaces (`#0B0F17`), and focused visual contrast.
2. **Confident rather than flashy:** Clear typography and explicit evidence badges over decorative animations.
3. **Progressive rather than overwhelming:** 6-stage progressive disclosure workflow revealing information as confidence builds.
4. **Explainable rather than magical:** 3-part structured developer explanations linked directly to telemetry node IDs.
5. **Functional rather than decorative:** Every visual indicator answers: *What happened? Why did it fail? What is the fix?*

---

## 2. Color System & Design Tokens

### 2.1 Palette Specifications (`tailwind.config` / `globals.css`)

```css
:root {
  /* Surface Colors */
  --bg-base: #0B0F17;          /* Primary dark canvas */
  --bg-surface: #111827;       /* Card surface */
  --bg-canvas: #1F2937;        /* Nested container surface */

  /* Border Colors */
  --border-subtle: #374151;    /* Standard dividers */
  --border-strong: #4B5563;    /* Structural borders */

  /* Text Colors */
  --text-primary: #F9FAFB;     /* High contrast headings */
  --text-secondary: #9CA3AF;   /* Body text & labels */

  /* Semantic Accent Highlights */
  --color-root-cause: #EF4444; /* Glowing Red - Root Cause Node */
  --color-evidence: #F59E0B;   /* Amber - Telemetry Evidence */
  --color-critical: #EAB308;   /* Yellow - Critical Path Edge */
  --color-success: #10B981;    /* Emerald Green - Verified Fix */
}
```

---

## 3. Typography & Hierarchy

### 3.1 Font Families
- **Display & Headings:** `Space Grotesk` (Google Font) — Bold, uppercase, tracking-wider for crisp technical titles.
- **Body & Interface:** `Inter` (Google Font) — Clean, highly readable sans-serif for explanations and cards.
- **Code & Telemetry:** `JetBrains Mono` (Google Font) — Monospace font for node IDs, timestamps, stack traces, and git diffs.

---

## 4. UI Component Library

### 4.1 Buttons & Controls
- **Primary Action Button:** Solid dark surface (`#F9FAFB` text on `#111827`), 2px border `#4B5563`, brutalist offset shadow `shadow-[2px_2px_0px_0px_#171717]`.
- **Verified Action Button:** Solid Emerald Green (`#10B981`), bold uppercase text, checkmark icon.
- **View Mode Toggle:** Header button toggling between `Guided Workflow Mode` and `Full Dashboard Mode`.

### 4.2 Diagnostic Explanation Cards
- 🔍 **Root Cause Card:** Dark red tint (`bg-red-950/20`), red border, monospace exception string.
- 💡 **Technical Analysis Card:** Amber tint (`bg-amber-950/20`), amber border, detailed code walkthrough.
- 🛠️ **Recommended Fix Card:** Emerald tint (`bg-emerald-950/20`), emerald border, step-by-step instructions.

### 4.3 Git Diff Viewer Component (`suggested-fix.tsx`)
- Dark black background (`#000000`), monospace font.
- Green text (`#34D399`) for addition lines starting with `+`.
- Red text (`#F87171`) for deletion lines starting with `-`.
- One-click copy button with "Copied!" feedback state.
