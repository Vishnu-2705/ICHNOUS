# ICHNOUS — The Causal Debugger for Autonomous AI Systems

Every other observability tool shows you what happened. ICHNOUS shows why—and gives you the fix.

## Authoritative Contract

`AGENTS.md` in the repository root is the authoritative contributor contract for all team members. All API schemas, naming conventions, fixture IDs, routes, and ownership boundaries defined in `AGENTS.md` must be followed strictly.

## Team Ownership

- **Person 1**: FastAPI backend, execution graph construction, causal walk algorithms, anomaly detection, root-cause ranking, LLM diagnosis call, evidence validation, and regression test generator. Runs on `http://localhost:8000`.
- **Person 2**: Next.js single-page frontend, React Flow causal graph visualization, diagnosis presentation cards, raw JSON viewer toggle, regression test viewer, and API integration client. Runs on `http://localhost:3000`.

## Repository Structure

```text
ICHNOUS/
├── AGENTS.md
├── README.md
├── .gitignore
├── backend/
└── frontend/
```

## Local Development Ports

- **Backend (FastAPI)**: `http://localhost:8000`
- **Frontend (Next.js)**: `http://localhost:3000`
