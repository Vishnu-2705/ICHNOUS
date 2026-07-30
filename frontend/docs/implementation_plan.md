# Pixel Perfect Implementation Plan

The application is functionally complete and production verified.

---

## Source of Truth

Use the attached reference image as the **visual source of truth**.
Use the existing project documentation as the **behavioral source of truth**:
- Product Constitution
- UX Architecture
- Visual Identity
- Design System
- Frontend Implementation

---

## Objective

Implement the current UI until it is visually indistinguishable from the supplied reference.

Treat the reference exactly like a Figma file handed to a frontend engineer.

---

## Implementation Philosophy

**Prefer refinement over replacement.**

If an existing component can be visually refined to match the reference, improve it rather than rebuilding it.
Preserve component identity, state management, accessibility, and interactions.
Minimize code churn while maximizing visual fidelity.

---

## Frozen Systems

Do **NOT** modify:
- Backend API
- React Query
- RevealContext
- GraphMapper
- Animation sequence
- Investigation logic
- Information architecture
- Component hierarchy

*Only CSS, spacing, typography, sizing, borders, shadows, and layout proportions may change.*

---

## Engineering Constraints

Favor CSS and styling refinements over structural code changes.
Do not replace existing components unless visual parity cannot be achieved through refinement.
Avoid unnecessary refactoring.
Preserve existing architecture, file organization, and component APIs.

---

## Keyboard Shortcuts

- `Shift + R`: Trigger Replay Investigation
- `Shift + S`: Skip Animation
- `Enter` / `Space`: Toggle Node Inspector
- `Esc`: Clear Selection / Collapse Inspector

---

## Verification Plan

### Automated Tests
- `npm run build` verified clean build with 0 TypeScript or CSS compilation errors.

### Manual Verification
- Visual side-by-side comparison against the reference mockup image at 100% zoom.
- Tested keyboard shortcuts (`Shift + R`, `Shift + S`).

---

## Definition of Done

The implementation is complete. A side-by-side comparison shows zero visual or functional defects.
