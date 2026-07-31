# Backend Architecture & Schema Documentation — TraceMind / ICHNOUS

**Product Title:** TraceMind / ICHNOUS — Backend Data Models, Session Manager, & Schemas  
**Document Version:** 1.0.0 (Production Release)  
**Status:** Approved Technical Single Source of Truth

---

## 1. Data Models & Entity Schemas

### 1.1 Core Session Schemas (`backend/models/session.py`)

#### `SessionStatus` (Enum)
```python
class SessionStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
```

#### `EventType` (Enum)
```python
class EventType(str, Enum):
    PLANNING = "planning"
    REASONING = "reasoning"
    TOOL_CALL = "tool_call"
    OBSERVATION = "observation"
    FINAL_ANSWER = "final_answer"
```

#### `TraceEvent` (Model)
| Field | Type | Description | Constraints / Default |
|---|---|---|---|
| `event_id` | `str` | Unique event ID | Required |
| `event_type` | `EventType` | Type of trace event | Required |
| `content` | `str` | Text content / payload | Required |
| `timestamp` | `str` | ISO 8601 UTC timestamp | Auto-generated |
| `metadata` | `Dict[str, Any]` | Telemetry metadata | Default `{}` |
| `agent_id` | `str` | Identifier of executing agent | Default `"default"` |

#### `TraceSession` (Model)
| Field | Type | Description | Constraints / Default |
|---|---|---|---|
| `session_id` | `str` | Unique session UUID | Required |
| `name` | `str` | Human-readable session name | Required |
| `description` | `str` | Session description | Default `""` |
| `status` | `SessionStatus` | Current lifecycle state | Default `CREATED` |
| `events` | `List[TraceEvent]` | Chronological trace events | Default `[]` |
| `created_at` | `str` | ISO 8601 UTC timestamp | Required |
| `updated_at` | `str` | ISO 8601 UTC timestamp | Required |
| `agent_ids` | `List[str]` | Participating agent IDs | Default `[]` |
| `tags` | `Dict[str, str]` | Custom metadata tags | Default `{}` |
| `diagnosis` | `Optional[DiagnosisResult]` | Grounded diagnosis result | Default `None` |
| `full_diagnosis` | `Optional[FullDiagnosisResponse]` | Full serialized diagnosis payload | Default `None` |

---

### 1.2 Core Trace & Diagnosis Schemas (`backend/models/trace.py`)

#### `SuggestedFix` (Model)
| Field | Type | Description | Constraints / Default |
|---|---|---|---|
| `type` | `str` | Fix type (`prompt_patch`, `tool_schema_fix`, `retry_policy`, `guardrail_addition`) | Required |
| `target` | `str` | Target file or component | Required |
| `diff` | `str` | Concrete 1-line `git-diff` patch | Required |

#### `DiagnosisResult` (Model)
| Field | Type | Description | Constraints / Default |
|---|---|---|---|
| `failure_category` | `str` | Taxonomy value (`Retrieval`, `Tool`, `Coordination`, `Memory`, `Prompt`, `None`) | Required |
| `confidence` | `float` | Confidence score between 0.0 and 1.0 | Required |
| `root_cause_node_id` | `str` | Root cause node ID | Required |
| `evidence_node_ids` | `List[str]` | List of evidence node IDs | Required |
| `explanation` | `str` | Structured 3-part developer explanation | Required |
| `suggested_fix` | `SuggestedFix` | Remediation fix object | Required |
| `grounded` | `bool` | Evidence grounding validation flag | Default `True` |

---

## 2. In-Memory Session Manager & Storage Layer (`backend/session/`)

### 2.1 Storage Implementation (`storage.py` & `manager.py`)
- **`SessionManager`:** Thread-safe in-memory session repository maintaining `self.sessions: Dict[str, TraceSession]`.
- **Session State Machine:** Validates allowed state transitions (`CREATED` -> `RUNNING` -> `COMPLETING` -> `COMPLETED`).
- **TTL Garbage Collection:** Automatically purges sessions older than `ttl_seconds` (default: 3600s / 1 hour).
- **Metric Aggregation:** Exposes real-time system metrics via `get_metrics()`:
  - `total_sessions`: Count of created sessions.
  - `active_sessions`: Count of currently running sessions.
  - `completed_sessions`: Count of completed sessions.
  - `failed_sessions`: Count of failed sessions.

---

## 3. Database Schema (`infrastructure/db/schema.sql`)

For production deployments using SQLite or PostgreSQL, the relational schema mirrors the in-memory Pydantic models:

```sql
CREATE TABLE IF NOT EXISTS sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'created',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    tags JSONB DEFAULT '{}',
    diagnosis JSONB
);

CREATE TABLE IF NOT EXISTS trace_events (
    event_id VARCHAR(64) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    event_type VARCHAR(32) NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    metadata JSONB DEFAULT '{}',
    agent_id VARCHAR(64) NOT NULL DEFAULT 'default'
);

CREATE INDEX idx_trace_events_session_id ON trace_events(session_id);
CREATE INDEX idx_sessions_status ON sessions(status);
```
