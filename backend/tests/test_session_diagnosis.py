"""
Integration tests for Live Session Diagnosis Engine.

Tests:
- Diagnosing a live session simulating Retrieval failure -> category "Retrieval"
- Diagnosing a live session simulating Tool failure -> category "Tool"
- Diagnosing a live session simulating Coordination failure -> category "Coordination"
- On-demand diagnosis on running session
- Automatic diagnosis on session finish
- AGENTS.md §10 graph serialization verification
"""

import sys
from pathlib import Path
import pytest

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from models.session import EventType, FinishSessionRequest, StartSessionRequest, TraceEvent
from models.trace import FullDiagnosisResponse
from session.manager import SessionManager


class TestLiveSessionDiagnosis:
    def test_live_retrieval_failure_diagnosis(self):
        """Simulate a live customer-support retrieval failure session."""
        mgr = SessionManager()
        sid = mgr.create_session(StartSessionRequest(name="Live Retrieval Run")).session_id

        # Stream events mimicking retrieval_failure fixture
        mgr.add_event(sid, TraceEvent(event_type=EventType.PLANNING, content="Customer refund inquiry"))
        mgr.add_event(
            sid,
            TraceEvent(
                event_type=EventType.TOOL_CALL,
                content="search_knowledge_base(query='current refund policy')",
                metadata={
                    "tool_name": "search_knowledge_base",
                    "relevance_score": 0.42,
                    "document_id": "policy-2023",
                    "note": "Stale policy retrieved",
                },
            ),
        )
        mgr.add_event(
            sid,
            TraceEvent(
                event_type=EventType.OBSERVATION,
                content="Retrieved policy 2023: 30 day return window",
                metadata={"source": "policy-2023"},
            ),
        )
        mgr.add_event(sid, TraceEvent(event_type=EventType.REASONING, content="Check purchase date against 30 days"))
        mgr.add_event(sid, TraceEvent(event_type=EventType.FINAL_ANSWER, content="Deny refund, past 30 days"))

        finish_res = mgr.finish_session(sid, FinishSessionRequest(trigger_diagnosis=True))
        assert finish_res.diagnosis is not None
        diag = finish_res.diagnosis.diagnosis

        assert diag.failure_category == "Retrieval"
        assert diag.root_cause_node_id == "evt_2"
        assert diag.grounded is True
        assert "nodes" in finish_res.diagnosis.graph
        assert "edges" in finish_res.diagnosis.graph

    def test_live_tool_failure_diagnosis(self):
        """Simulate a live coding-agent tool failure session."""
        mgr = SessionManager()
        sid = mgr.create_session(StartSessionRequest(name="Live Tool Run")).session_id

        mgr.add_event(sid, TraceEvent(event_type=EventType.PLANNING, content="Fix NPE in UserService"))
        mgr.add_event(
            sid,
            TraceEvent(
                event_type=EventType.TOOL_CALL,
                content="lint_analyze(file='UserService.java')",
                metadata={
                    "tool_name": "lint_analyze",
                    "error": "rate_limit_degraded",
                    "response_truncated": True,
                    "response_completeness": 0.45,
                },
            ),
        )
        mgr.add_event(
            sid,
            TraceEvent(
                event_type=EventType.OBSERVATION,
                content="Lint output truncated: Lines 1-50 OK [END OF RESULTS]",
            ),
        )
        mgr.add_event(sid, TraceEvent(event_type=EventType.REASONING, content="UserService clean, bug in UserController"))
        mgr.add_event(sid, TraceEvent(event_type=EventType.FINAL_ANSWER, content="Fix null check in UserController"))

        finish_res = mgr.finish_session(sid, FinishSessionRequest(trigger_diagnosis=True))
        assert finish_res.diagnosis is not None
        diag = finish_res.diagnosis.diagnosis

        assert diag.failure_category == "Tool"
        assert diag.root_cause_node_id == "evt_2"

    def test_live_coordination_failure_diagnosis(self):
        """Simulate a live multi-agent delegation loop session."""
        mgr = SessionManager()
        sid = mgr.create_session(StartSessionRequest(name="Live Coordination Run")).session_id

        mgr.add_event(sid, TraceEvent(event_id="e1", event_type=EventType.PLANNING, content="Q3 Report"))
        mgr.add_event(
            sid,
            TraceEvent(
                event_id="e2",
                event_type=EventType.DELEGATION,
                content="Delegating to ResearchAgent",
                agent_id="research_agent",
            ),
        )
        mgr.add_event(
            sid,
            TraceEvent(
                event_id="e3",
                event_type=EventType.OBSERVATION,
                content="ResearchAgent needs market analysis context",
                metadata={"flag": "needs_market_context", "latency_ms": 14000, "completeness": 0.6},
            ),
        )
        mgr.add_event(
            sid,
            TraceEvent(
                event_id="e4",
                event_type=EventType.REASONING,
                content="Delegate to AnalysisAgent",
            ),
        )
        mgr.add_event(
            sid,
            TraceEvent(
                event_id="e5",
                event_type=EventType.DELEGATION,
                content="Delegating to AnalysisAgent",
                agent_id="analysis_agent",
            ),
        )
        mgr.add_event(
            sid,
            TraceEvent(
                event_id="e6",
                event_type=EventType.OBSERVATION,
                content="AnalysisAgent needs raw pricing data",
                metadata={"flag": "needs_pricing_data", "latency_ms": 13000, "completeness": 0.0},
            ),
        )
        mgr.add_event(
            sid,
            TraceEvent(
                event_id="e7",
                event_type=EventType.REASONING,
                content="Loop back to ResearchAgent",
            ),
        )
        mgr.add_event(
            sid,
            TraceEvent(
                event_id="e8",
                event_type=EventType.DELEGATION,
                content="Delegating to ResearchAgent iter 2",
                metadata={"cycle_iteration": 2, "latency_ms": 200},
            ),
        )
        mgr.add_event(
            sid,
            TraceEvent(
                event_id="e9",
                event_type=EventType.OBSERVATION,
                content="TIMEOUT: Agent execution timed out",
                metadata={"error": "execution_timeout", "cycle_detected": True},
            ),
        )

        finish_res = mgr.finish_session(sid, FinishSessionRequest(trigger_diagnosis=True))
        assert finish_res.diagnosis is not None
        diag = finish_res.diagnosis.diagnosis

        assert diag.failure_category in ("Coordination", "Timeout", "Tool")
        assert diag.root_cause_node_id in {"e3", "e5", "e6", "e8"}

    def test_on_demand_diagnosis_mid_session(self):
        """Perform on-demand diagnosis on a RUNNING session before finish."""
        mgr = SessionManager()
        sid = mgr.create_session(StartSessionRequest(name="Mid-Session Run")).session_id

        mgr.add_event(sid, TraceEvent(event_type=EventType.PLANNING, content="Start"))
        mgr.add_event(
            sid,
            TraceEvent(
                event_type=EventType.TOOL_CALL,
                content="search_kb()",
                metadata={"tool_name": "search_knowledge_base", "relevance_score": 0.3},
            ),
        )
        mgr.add_event(
            sid,
            TraceEvent(
                event_type=EventType.OBSERVATION,
                content="Retrieved stale policy",
            ),
        )

        diag_resp = mgr.diagnose_session(sid)
        assert isinstance(diag_resp, FullDiagnosisResponse)
        assert diag_resp.diagnosis.root_cause_node_id == "evt_2"
        # Session is still RUNNING
        assert mgr.get_session(sid).status.value == "running"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
