<div align="center">

# 🚀 ICHNOUS

### Graph-native AI observability & causal debugging for autonomous agents

[![License: MIT](https://img.shields.io/badge/License-MIT-3B82F6.svg)](#-license)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](#-installation)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](#-technology-stack)
[![Status](https://img.shields.io/badge/Status-Research%20%2F%20Hackathon-F59E0B.svg)](#-roadmap)

*Named for* ***ichnos*** *— Greek for "trace" or "footprint": the marks a process leaves behind.*

</div>

---

## 📖 Table of contents

- [Vision](#-vision)
- [Key features](#-key-features)
- [Architecture](#-architecture)
- [Regression Intelligence Engine](#-regression-intelligence-engine)
- [Project structure](#-project-structure)
- [Installation](#️-installation)
- [Example API](#-example-api)
- [Technology stack](#-technology-stack)
- [Roadmap](#️-roadmap)
- [License](#-license)
- [Contributors](#-contributors)

---

## 🌍 Vision

**ICHNOUS** is an AI observability platform designed to diagnose failures in
autonomous AI agents by converting execution traces into heterogeneous
graphs, performing graph-based causal reasoning, and predicting regression
risk using a Graph Neural Network (GNN).

Unlike traditional log viewers, ICHNOUS reasons over **execution structure**
— not isolated events. A failure isn't a line in a log; it's a node in a
graph, connected by cause to everything that led to it.

---

## ✨ Key features

| | |
|---|---|
| 🧠 | Graph-based execution trace construction |
| 🔍 | Root-cause localization |
| 🤖 | Heterogeneous Graph Transformer (HGT) inference pipeline |
| 📈 | Regression Intelligence Engine |
| 💾 | Vector memory bank for similar-execution retrieval |
| 🌐 | FastAPI backend |
| 📊 | Interactive dashboard |
| 🔬 | Explainability via GNNExplainer |
| ⚡ | Modular, swappable architecture |

---

## 🏗 Architecture

```
                     ┌─────────────┐
                     │   AI Agent  │
                     └──────┬──────┘
                            │
                            ▼
                  ┌───────────────────┐
                  │  Execution Trace   │
                  └─────────┬──────────┘
                            │
                            ▼
                ┌────────────────────────┐
                │  Execution Graph Builder │
                └────────────┬─────────────┘
                            │
                            ▼
                  ┌────────────────────┐
                  │  Feature Extraction │
                  └──────────┬──────────┘
                            │
                            ▼
          ┌──────────────────────────────────────┐
          │  Heterogeneous Graph Transformer (HGT) │
          └────────────────────┬────────────────────┘
                            │
                            ▼
          ┌──────────────────────────────────────┐
          │   Regression Intelligence Engine        │
          │   ├── Regression risk                   │
          │   ├── Failure category                  │
          │   ├── Root cause                        │
          │   ├── Confidence                        │
          │   └── Vulnerable nodes                  │
          └────────────────────┬────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  GNNExplainer  │
                    └───────┬────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │  Developer Dashboard  │
                └───────────────────────┘
```

---

## 🧠 Regression Intelligence Engine

The engine transforms execution graphs into graph embeddings and predicts:

| Output | Description |
|---|---|
| **Regression risk** | Likelihood of regression |
| **Failure category** | Retrieval / Tool / Coordination / Reasoning |
| **Confidence** | Prediction confidence |
| **Root cause** | Most influential node |
| **Vulnerable nodes** | Ranked node importance |
| **Similar executions** | Retrieved from vector memory |

> ⚠️ **Note:** If using placeholder model weights, predictions demonstrate the inference pipeline but are not yet trained on production datasets.

---

## 📂 Project structure

```
backend/
 ├── api/
 ├── graph/
 ├── gnn/
 │    ├── encoder.py
 │    ├── explainer.py
 │    ├── heads.py
 │    ├── memory_bank.py
 │    └── pytorch_model.py
 ├── regression/
 ├── models/
 └── tests/
frontend/
```

---

## ⚙️ Installation

```bash
git clone https://github.com/your-org/ichnous.git
cd ichnous
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Run:

```bash
uvicorn backend.main:app --reload
```

---

## 📡 Example API

```
POST /traces/{trace_id}/gnn-predict
```

**Example response:**

```json
{
  "regression_probability": 0.19,
  "failure_category": "Retrieval",
  "confidence_score": 0.94,
  "predicted_root_cause_node_id": "node_5"
}
```

---

## 🔬 Technology stack

| Layer | Technology |
|---|---|
| Backend | FastAPI |
| ML | PyTorch |
| Graph | NetworkX, Neo4j |
| GNN | HGT (Heterogeneous Graph Transformer) |
| Explainability | GNNExplainer |
| Memory | Vector memory bank |

---

## 🗺️ Roadmap

- [ ] Execution Graph Builder
- [ ] Root Cause Engine
- [ ] GNN Regression Intelligence Engine
- [ ] Explainability
- [ ] Train HGT on labeled execution graphs
- [ ] Continuous online learning
- [ ] Production model registry

---

## 📜 License

MIT License.

## 👥 Contributors

Built for AI observability research and hackathon innovation.

<div align="center">

*ICHNOUS — follow the footprints, find the cause.*

</div>
