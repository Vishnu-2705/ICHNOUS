# Technical Debt Report — TraceMind / ICHNOUS

**Product Title:** TraceMind / ICHNOUS — Technical Debt & Refactoring Inventory  
**Document Version:** 1.0.0 (Production Release)  
**Status:** Complete Audit

---

## 1. Technical Debt Inventory

### 1.1 In-Memory State Retention
- **Description:** Sessions and upload SHA-256 caches (`_UPLOAD_CACHE`) are stored in RAM within the FastAPI application process (`manager.py`, `upload.py`).
- **Impact:** Server restart clears active in-memory sessions (though static fixtures persist).
- **Remediation:** Introduce Redis or SQLite persistent session backing for multi-process worker deployments.

### 1.2 Subprocess Sandbox Execution Isolation
- **Description:** `_execute_code_in_sandbox` executes uploaded Python code using `subprocess.run([sys.executable, file_path])`.
- **Impact:** While pattern checks (`os.system`, `subprocess.Popen`) and process timeouts (3s) prevent basic security abuses, a containerized gVisor / Docker container sandbox is recommended for production multi-tenant environments.
- **Remediation:** Implement Docker-in-Docker or WASM sandbox isolation for production deployment.
