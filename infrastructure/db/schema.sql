-- TraceMind Enterprise Database Migration Schema (PostgreSQL 16)
-- Spec Version: 1.0.0-PROD

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enums
CREATE TYPE session_status_enum AS ENUM (
    'created', 'running', 'completing', 'completed', 'failed', 'expired'
);

CREATE TYPE event_type_enum AS ENUM (
    'planning', 'llm_call', 'llm_response', 'tool_call', 'tool_response',
    'observation', 'reasoning', 'decision', 'delegation', 'memory_read',
    'memory_write', 'error', 'final_answer', 'custom'
);

CREATE TYPE failure_category_enum AS ENUM (
    'Planning', 'Memory', 'Retrieval', 'Reasoning', 'Context',
    'Hallucination', 'Specification', 'Tool', 'Safety', 'Verification',
    'Coordination', 'Timeout', 'External_API', 'Human', 'Unknown'
);

-- Workspaces Table (Tenant Isolation & Auth Keys)
CREATE TABLE IF NOT EXISTS workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    api_key_hash VARCHAR(512) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT clock_timestamp()
);

-- Default system workspace
INSERT INTO workspaces (id, name, slug, api_key_hash)
VALUES ('00000000-0000-0000-0000-000000000001', 'Default Workspace', 'default', 'default_key_hash')
ON CONFLICT (slug) DO NOTHING;

-- Sessions Table
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status session_status_enum NOT NULL DEFAULT 'created',
    event_count INT DEFAULT 0,
    agent_ids JSONB DEFAULT '[]'::jsonb,
    tags JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ DEFAULT clock_timestamp(),
    finished_at TIMESTAMPTZ,
    CONSTRAINT unq_workspace_session UNIQUE (workspace_id, session_id)
);

CREATE INDEX IF NOT EXISTS idx_sessions_workspace_status ON sessions(workspace_id, status);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at DESC);

-- Trace Events Table
CREATE TABLE IF NOT EXISTS trace_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    event_id VARCHAR(255) NOT NULL,
    parent_event_id VARCHAR(255),
    event_type event_type_enum NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    reads_from JSONB DEFAULT '[]'::jsonb,
    agent_id VARCHAR(255),
    sequence_number INT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT clock_timestamp(),
    CONSTRAINT unq_session_event UNIQUE (session_id, event_id)
);

CREATE INDEX IF NOT EXISTS idx_trace_events_session_seq ON trace_events(session_id, sequence_number ASC);
CREATE INDEX IF NOT EXISTS idx_trace_events_parent ON trace_events(session_id, parent_event_id);

-- Diagnosis Results Table
CREATE TABLE IF NOT EXISTS diagnosis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID UNIQUE NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    failure_category failure_category_enum NOT NULL,
    confidence NUMERIC(3,2) NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    root_cause_node_id VARCHAR(255) NOT NULL,
    evidence_node_ids JSONB NOT NULL,
    explanation TEXT NOT NULL,
    suggested_fix JSONB NOT NULL,
    grounded BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT clock_timestamp()
);
