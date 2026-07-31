# Testing Strategy & QA Plan — TraceMind / ICHNOUS

**Product Title:** TraceMind / ICHNOUS — Test Architecture & Quality Assurance Matrix  
**Document Version:** 1.0.0 (Production Release)  
**Status:** Approved QA Strategy

---

## 1. Test Suite Architecture

TraceMind includes an extensive suite of **166 automated Pytest backend tests** (33 test modules) and frontend integration test specs.

### 1.1 Test Coverage Matrix

| Test Suite Module | Target Subsystem | Tests Count | Coverage Focus |
|---|---|---|---|
| `test_anomaly_detection.py` | Causal Analyzer | 8 | Exception, truncation, & rate limit detection |
| `test_backward_walk.py` | Causal Walk Engine | 6 | Multi-step backward path traversal |
| `test_critical_path.py` | Graph Subsystem | 5 | Longest directed path calculation |
| `test_gnn_engine.py` | GNN Intelligence | 12 | HGT PyTorch model, GNNExplainer, Memory Bank |
| `test_upload_api.py` | Ingestion Router | 10 | File size, disallowed patterns, SHA-256 caching |
| `test_verifier.py` | Sandbox Verifier | 8 | Closed-loop patch execution & verification |
| `test_agent365_*` | OTel & Agent 365 | 45 | OTLP, Phoenix, Webhooks, Neo4j, CLI adapters |
| `test_prd_requirements.py` | PRD Compliance | 14 | End-to-end PRD requirement verification |
| **Total Automated Suite** | **Entire System** | **166 Passed** | **100% Core Functionality** |

---

## 2. Command Reference
- **Run Complete Backend Test Suite:** `cd backend && python3 -m pytest`
- **Run Frontend Tests:** `cd frontend && npm test`
- **Run Production Build Verification:** `cd frontend && npm run build`
