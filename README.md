# TraceMind (ICHNOUS) — The Causal Debugger for Autonomous AI Systems

> TraceMind shows why something failed in an autonomous agent run — and gives a grounded, testable fix.
>
> This repository (ICHNOUS) holds the TraceMind MVP: a 24-hour hackathon-quality prototype that takes a recorded agent trace, builds a causal execution graph, deterministically finds a ranked root cause, calls an LLM once to produce a grounded explanation and fix, and emits a regression test artifact that reproduces the failure.

Status: active prototype — backend + frontend scaffolded. Work done so far is listed under "What we implemented".

---

Table of contents
- Project summary
- Hackathon constraints & design decisions
- What we implemented so far
- Architecture overview
- Getting started (local)
  - Backend (FastAPI)
  - Frontend (Next.js)
- Canonical API (what the frontend calls)
- Trace fixtures
- Data models & types
- Testing & verification
- How to contribute
- Roadmap (next steps)
- License

---

## Project summary

TraceMind accepts a recorded trace of an autonomous AI-agent run and produces:

1. A reconstructed causal execution graph.
2. A single ranked root-cause node (deterministic ranking).
3. A failure category from a small, fixed taxonomy.
4. Structurally grounded evidence nodes and causal paths.
5. A confidence score for the diagnosis.
6. A concrete suggested fix (LLM-backed, single call per diagnosis).
7. A JSON regression-test artifact that can reproduce the failure deterministically.

The primary project goal is to deliver a working end-to-end demo (MVP) within the hackathon constraints — reliability and deterministic fixture behavior take precedence over production-scale concerns.

---

## Hackathon constraints & design decisions

These constraints shaped every design choice:

- 24-hour timebox for the MVP; prioritize a single end-to-end demo.
- Team size: 2 contributors (backend owner + frontend owner).
- Architecture: one FastAPI backend and one Next.js frontend.
- Storage: in-memory dictionaries or SQLite only (no external infra).
- No authentication.
- No cloud infra.
- LLM usage: strictly one LLM call per diagnosis (LLM acts as explanation/fix layer only).
- Data source: three hardcoded trace fixtures (deterministic demo).
- Keep network and runtime dependencies minimal and reproducible.

We intentionally avoid adding databases (beyond SQLite), vector stores, external ingestion pipelines, or orchestration tools in this MVP.

---

## What we implemented so far

(What we've completed as part of the prototype — a snapshot of the current repository state.)

Backend (Python / FastAPI)
- Pydantic domain models for trace nodes, traces, diagnosis responses, and regression artifacts.
- Three deterministic trace fixtures (stored as JSON) used for demo runs.
- FastAPI application with REST endpoints for:
  - Listing available fixtures
  - Retrieving raw trace JSON
  - Requesting a diagnosis for a trace
- NetworkX-based graph builder to convert a trace into a directed causal graph.
- Deterministic structural analyzer components:
  - Anomaly detection rules (structural & value-based heuristics).
  - Critical-path extraction.
  - Backward causal walk to gather candidate root causes.
  - Divergence scoring and deterministic root-cause ranking.
- Single, grounded LLM call integration (configurable):
  - LLM is used only once per diagnosis to generate human-readable explanation, fix, and the regression JSON.
  - LLM output is validated against a JSON schema (Pydantic) and groundedness checks are in place.
- Regression-test artifact generator: deterministic JSON artifact that encodes the minimal reproduction scenario.
- Backend unit tests to verify deterministic behavior on fixture traces.

Frontend (TypeScript / Next.js)
- Single-page UI scaffold:
  - Trace selector (choose one of the fixtures)
  - Raw JSON trace viewer
  - Network/graph visualization view (client-side rendering of nodes/edges)
  - Diagnosis card showing root cause, evidence, failure category, confidence, and suggested fix
  - Regression artifact viewer (raw JSON)
- Shared TypeScript types that mirror the backend Pydantic models.
- Mock API mode to allow frontend development without running the backend.
- Loading / error / empty states handled for the main flows.

Integration & Shared
- API contract frozen for the current integration window: Pydantic <-> TypeScript types are semantically matched.
- CORS enabled for local development.
- Basic end-to-end manual demo flow validated against the three fixtures.

---

## Architecture overview

Trace fixture -> FastAPI route -> NetworkX graph builder -> Deterministic structural analyzer (anomaly detection / critical-path / backward walk / ranking) -> single grounded LLM call -> schema & evidence validation -> Diagnosis + Regression artifact -> Next.js frontend

Notes:
- The LLM is an explanation/fix generator only. The root-cause detection is entirely structural/deterministic.
- The regression artifact is intended to be machine-executable (JSON) to reproduce failure deterministically for the demo.

---

## Getting started (local development)

Prerequisites
- Node.js (16+/18+ recommended)
- Python 3.10+
- pip or poetry (we use pip in the instructions)
- (Optional) virtualenv

1) Clone the repo
```bash
git clone https://github.com/Vishnu-2705/ICHNOUS.git
cd ICHNOUS
```

2) Backend: set up and run
```bash
# create virtualenv (optional)
python -m venv .venv
source .venv/bin/activate

# install
pip install -r backend/requirements.txt

# run migrations (if any) - none expected for prototype

# start the FastAPI backend (development)
uvicorn backend.main:app --reload --port 8000
```

Default backend ports/configs are in `backend/.env.example` (if present). The API is available at http://localhost:8000.

3) Frontend: set up and run
```bash
cd frontend
npm install
npm run dev
```

Frontend will start (by default) at http://localhost:3000 and will call the backend at http://localhost:8000 (CORS is enabled for localhost during development).

4) Mock mode
- The frontend supports a mock API mode (see `frontend/.env.local` or UI toggle). Use this when backend is not running.

---

## Canonical API (implemented endpoints)

These endpoints are currently implemented on the backend. The TypeScript client wraps them with types that mirror Pydantic models.

- GET /api/fixtures
  - Returns: list of available fixture metadata (id, name, description)
- GET /api/fixtures/{fixture_id}
  - Returns: full raw trace JSON for the fixture
- POST /api/diagnose
  - Body: { "trace_id": "<fixture_id>" } OR { "trace": <trace_json_inline> }
  - Action: Builds graph, runs deterministic analyzer, makes a single LLM call for explanation/fix, validates LLM output, and returns DiagnosisResponse
  - Returns: DiagnosisResponse JSON:
    - root_cause: { id, node_type, summary }
    - failure_category: one of the fixed taxonomy
    - evidence: list of structural evidence nodes/paths
    - confidence: float (0.0 - 1.0)
    - suggested_fix: text (LLM generated)
    - regression_artifact: JSON (machine-readable reproduction)
    - diagnostics: analyzer metadata (scores, reason traces)

Example usage:
```bash
curl -X POST "http://localhost:8000/api/diagnose" \
  -H "Content-Type: application/json" \
  -d '{"trace_id":"fixture_1"}'
```

---

## Trace fixtures

There are three hardcoded trace fixtures used for deterministic demo runs. Fixtures live under `backend/fixtures/` and are stable — do not rename fixture IDs without coordinating frontend TypeScript types.

Each fixture contains:
- an ordered list of TraceNode objects (id, type, timestamp, payload metadata)
- explicit causal links (when applicable) or raw sequential events (the analyzer constructs causal edges)
- annotations used to test anomaly detection rules

We designed fixtures to exercise:
- Tool-call failures (external API errors)
- Planning logic failures (bad reasoning leading to wrong plan)
- Delegation/routing mistakes (wrong agent routing leads to missing data)

---

## Data models & types

Domain-level node types (allowed values)
- plan
- tool_call
- observation
- reasoning
- decision
- delegation
- final_answer

Important: Do not introduce `retrieval` as a node type in the MVP; represent retrieval as a `tool_call` or `observation` with metadata like `tool_name`, `document_version`, and `relevance_score`.

Shared models:
- TraceNode (id, node_type, timestamp, text, metadata)
- Trace (id, title, nodes[], edges[])
- DiagnosisResponse (root_cause, failure_category, evidence, confidence, suggested_fix, regression_artifact)
- RegressionArtifact (structured JSON reproduction spec)

The backend Pydantic models live in `backend/models.py` and the frontend TypeScript interfaces live in `frontend/src/types/`. Keep these synced when making contract changes.

---

## Testing & deterministic verification

- Backend unit tests validate deterministic outputs for the three fixtures (tests live in `backend/tests/`).
- Frontend integration dev flow uses mock API data to verify UI behavior without the backend.
- Before demoing, run:
  - Backend tests:
    ```bash
    cd backend
    pytest -q
    ```
  - Frontend static checks:
    ```bash
    cd frontend
    npm run lint
    npm run test
    ```

---

## How to contribute

- Keep API contract changes synchronized: any change to a Pydantic model must be reflected in the TypeScript types in the same PR.
- Preserve fixture IDs and node IDs — many deterministic tests rely on them.
- Keep LLM usage to at most one call per diagnose request.
- If you add a new fixture, add deterministic test cases that assert expected diagnosis outputs (root cause id, category, confidence).
- Use small PRs that touch either backend-only or frontend-only code where possible. For breaking schema changes coordinate in a single integration window (both backend & frontend updates together).

Suggested flow:
1. Fork the repo.
2. Create a branch `feat/your-feature` or `fix/issue-###`.
3. Make changes; run tests locally.
4. Open a PR describing the change and include updated fixtures/tests if applicable.

---

## Roadmap (next steps / TODO)

Priority items:
- Implement stricter groundedness checks on LLM outputs (more schema assertions & counter-evidence checks).
- Improve graph visualization with edge labels and causal weight visualization.
- Add a small CLI to run a diagnosis locally and output the regression artifact to stdout/file.
- Add a small harness that can re-run the regression artifact to confirm it reproduces the fixture failure.
- Add a minimalistic demo script that cycles through fixtures and saves HTML/PDF of the diagnosis for easy demoing.

Lower priority / out of scope for MVP:
- No external DB, vector stores, nor cloud infra planned for this hackathon MVP.

---

## Where things live (important paths)

- backend/
  - main.py — FastAPI app entrypoint
  - models.py — Pydantic models and schema
  - analyzer/ — NetworkX builder and deterministic analyzer logic
  - fixtures/ — the three demo traces
  - tests/ — backend tests
- frontend/
  - pages/ — Next.js pages
  - src/components/ — React components (Graph, TraceViewer, DiagnosisCard)
  - src/api/ — client API wrappers (mirrors backend endpoints)
  - src/types/ — TypeScript types that match backend models

---

## A note about LLM usage & determinism

We use the LLM strictly as an explanation/fix generator so our structural root-cause logic remains deterministic and testable. Each diagnose request calls the LLM once. The backend includes schema validation and simple groundedness heuristics to detect hallucinations or schema violations. For the demo, run the diagnosis on the 3 fixtures and verify the outputs are consistent.

---

## Contact, credits & ownership

Primary contributors:
- Person 1 — Backend and intelligence engine owner
- Person 2 — Frontend, visualization, and API integration owner

Both contributors share responsibility for freezing the API contract, ensuring fixtures remain stable, and making the demo deterministic and reproducible.

---

## License

This prototype is released under the MIT License. See LICENSE for details.

---

If you'd like, I can:
- Generate a README file in the repository now (commit it),
- Produce a short script to run the three fixtures and dump diagnosis outputs to files for demo use,
- Or draft the demo script and screenshot instructions for the presentation.

Tell me which of these you want me to do next and I'll proceed.
