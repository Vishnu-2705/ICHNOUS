# ICHNOUS PRODUCT CONSTITUTION

## Positioning
Ichnous is an AI Investigation Workspace that reconstructs execution trails, uncovers the true root cause of failures, and guides developers from evidence to resolution.

## Product Mission
Ichnous exists to reduce the cognitive effort required to debug autonomous AI systems. Instead of forcing developers to manually inspect execution traces, Ichnous reconstructs the execution, uncovers the causal chain of failure, and guides users from evidence to understanding. The goal is not to visualize data. The goal is to create understanding. Every interaction, animation, and interface element should reduce uncertainty and increase confidence.

## Product North Star
Ichnous should make developers feel like they understand an AI failure—not that they are debugging one. 
If users leave the application thinking *"I know exactly why this happened,"* the product has succeeded.
If users leave thinking *"I need to inspect more logs,"* the product has failed.

## Design Values
The interface should be:
- Calm rather than noisy.
- Confident rather than flashy.
- Progressive rather than overwhelming.
- Explainable rather than magical.
- Functional rather than decorative.
- Enterprise-grade rather than experimental.
*(Whenever there is a design decision, these values take precedence over visual novelty.)*

## Visual Personality
Ichnous should feel like: **70% Linear, 20% Raycast, 10% Neo Brutalism.**
The UI should prioritize:
- Large whitespace
- Strong hierarchy
- Bold typography
- Subtle motion
- High contrast
- Thick borders
- Offset shadows
- Minimal color

The product should **never** resemble: Cyberpunk, Glassmorphism, Gaming UI, Analytics dashboards, or Sci-fi interfaces.

## Interaction Philosophy
The interface should never surprise the user. Every interaction should feel inevitable.
Users should always know: Where they are. What changed. What happens next.
Motion should reinforce understanding. Never use animation purely for aesthetics.

## Core UX Principles
### The Reveal Principle
The value of Ichnous is transforming complex AI execution into an understandable investigation. The investigation should progressively reveal evidence until the root cause becomes obvious.

### Progressive Confidence
The interface should become more confident as the investigation progresses. 
- *Beginning:* The graph is neutral.
- *During Investigation:* Evidence is highlighted.
- *After Investigation:* The root cause is emphasized.
- *Finally:* The recommendation and safeguard appear.

### Focus First
At every stage of the investigation, the interface should reduce complexity rather than increase it. Instead of exposing the full execution immediately, progressively direct the user's attention toward the most relevant evidence.

## Layout Constraints
**Desktop-first. Persistent three-column workspace.**
- Left Sidebar (18%)
- Investigation Canvas (52%)
- Investigation Summary (30%)
- Execution Timeline remains attached to the bottom of the workspace.

The layout must remain stable during interaction. Avoid moving major interface regions after the investigation begins.

## Motion Principles
Motion exists to communicate understanding—not decoration. Every animation must answer: What is happening? What changed? Where should the user look next?
- Keep animations between 150–400ms.
- Use easing that feels smooth and confident.
- Never animate everything simultaneously.
- Priority: 1. Graph reconstruction, 2. Evidence highlight, 3. Camera movement, 4. Root cause emphasis, 5. Investigation Summary reveal, 6. Timeline synchronization.

## Engineering Constraints
The backend is already implemented. The frontend is a presentation layer.
The frontend must **never**: Calculate diagnoses, Infer confidence, Generate evidence, Reconstruct graphs, or Duplicate backend logic. It only visualizes and communicates backend output.

## Application States & Component Responsibilities
### States
1. **Empty:** No case selected.
2. **Investigating:** Active reconstruction.
3. **Revealed:** Root cause identified.
4. **Reviewing:** User inspecting evidence.
5. **Completed:** Safeguard generated.

### Component Responsibilities
- **CaseSidebar:** Select investigations, status, search, filters. *Never graph logic.*
- **InvestigationCanvas:** Render graph, camera, node highlights, replay. *Never business data.*
- **InvestigationSummary:** Root Cause, Evidence, Recommendation, Safeguard. *Never calculates logic.*
- **ExecutionTimeline:** Chronological mapping, timeline sync. *Always synchronized with graph.*

## Non-Negotiable Principles
- The graph is the source of truth.
- The Investigation Summary explains the graph.
- The backend owns all reasoning.
- The frontend never invents evidence.
- The interface always guides the user.
- Every screen must answer: What happened? Why did it happen? What should I do next?

## Success Criteria
A first-time user should:
- Understand **what failed** within **3 seconds**.
- Identify the **root cause** within **8 seconds**.
- Understand the **recommendation** within **15 seconds**.
*(If these goals are not met, simplify the interface.)*

## Definition of Done
The implementation is complete when:
- `[x]` A user can select a Case.
- `[x]` The Investigation automatically begins.
- `[x]` The graph reconstructs visually.
- `[x]` Evidence is progressively highlighted.
- `[x]` The Root Cause is unmistakable.
- `[x]` The Investigation Summary explains the result.
- `[x]` A Safeguard can be generated.
- `[x]` Replay Investigation works.
- `[x]` The product communicates its value in under five seconds.
