"""
Live Sessions REST API Router for TraceMind.

Exposes REST endpoints for the live agent runtime:
- POST /sessions/start                 -> Create a new live session
- POST /sessions/{id}/events           -> Ingest a single agent event
- POST /sessions/{id}/events/batch     -> Ingest a batch of events (up to 100)
- POST /sessions/{id}/finish           -> Finish session and trigger diagnosis
- POST /sessions/{id}/diagnose         -> Run on-demand diagnosis on active/completed session
- GET  /sessions                       -> List session summaries (paginated + status filter)
- GET  /sessions/{id}                  -> Get full session state
- GET  /sessions/{id}/graph            -> Get serialized NetworkX execution graph
- GET  /sessions/{id}/events           -> Get paginated list of session events
- DELETE /sessions/{id}                -> Delete session resources
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)

try:
    from models.session import (
        EventType,
        FinishSessionRequest,
        FinishSessionResponse,
        IngestBatchRequest,
        IngestEventRequest,
        IngestEventResponse,
        PaginatedEvents,
        PaginatedSessions,
        SessionStatus,
        SessionSummary,
        StartSessionRequest,
        StartSessionResponse,
        TraceEvent,
        TraceSession,
    )
    from models.trace import FullDiagnosisResponse
    from session.diagnosis import serialize_session_graph
    from session.manager import SessionManager
    from session.websocket_hub import WebSocketHub
except ImportError:
    from backend.models.session import (
        EventType,
        FinishSessionRequest,
        FinishSessionResponse,
        IngestBatchRequest,
        IngestEventRequest,
        IngestEventResponse,
        PaginatedEvents,
        PaginatedSessions,
        SessionStatus,
        SessionSummary,
        StartSessionRequest,
        StartSessionResponse,
        TraceEvent,
        TraceSession,
    )
    from backend.models.trace import FullDiagnosisResponse
    from backend.session.diagnosis import serialize_session_graph
    from backend.session.manager import SessionManager
    from backend.session.websocket_hub import WebSocketHub


router = APIRouter(prefix="/sessions", tags=["sessions"])

# Singleton WebSocket connection hub and session manager
ws_hub = WebSocketHub()
session_manager = SessionManager(ws_hub=ws_hub)


def get_session_manager() -> SessionManager:
    """Return singleton SessionManager instance."""
    return session_manager


@router.post(
    "/start",
    response_model=StartSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new live agent trace session",
)
async def start_session(request: StartSessionRequest) -> StartSessionResponse:
    """Create a new session container and allocate its execution graph."""
    mgr = get_session_manager()
    try:
        return mgr.create_session(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/demo/{scenario}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger a live simulated agent run for demonstration",
)
async def trigger_live_demo(scenario: str) -> Dict[str, str]:
    """
    Spawns a live simulated agent run in a background thread.
    Supported scenarios: retrieval_failure, tool_failure, coordination_failure
    """
    valid_scenarios = {"retrieval_failure", "tool_failure", "coordination_failure"}
    if scenario not in valid_scenarios:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scenario '{scenario}'. Allowed: {', '.join(valid_scenarios)}",
        )

    def _run_demo():
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).resolve().parent.parent
        sdk_dir = backend_dir.parent / "sdk"
        if str(sdk_dir) not in sys.path:
            sys.path.insert(0, str(sdk_dir))
        from examples.demo_agent import (
            run_coordination_failure_scenario,
            run_retrieval_failure_scenario,
            run_tool_failure_scenario,
        )

        backend_url = "http://localhost:8000"
        if scenario == "retrieval_failure":
            run_retrieval_failure_scenario(backend_url)
        elif scenario == "tool_failure":
            run_tool_failure_scenario(backend_url)
        elif scenario == "coordination_failure":
            run_coordination_failure_scenario(backend_url)

    # Run demo asynchronously in background thread so HTTP call returns immediately
    asyncio.create_task(asyncio.to_thread(_run_demo))

    return {
        "status": "started",
        "scenario": scenario,
        "message": f"Live agent simulation '{scenario}' started in background.",
    }


@router.post(
    "/{session_id}/events",
    response_model=IngestEventResponse,
    summary="Ingest a single agent event",
)
async def ingest_event(session_id: str, request: IngestEventRequest) -> IngestEventResponse:
    """
    Ingest a single event emitted by an AI agent into a live trace session.
    Incrementally updates the execution graph and auto-links dependency nodes.
    """
    mgr = get_session_manager()
    try:
        return mgr.add_event(session_id, request.event)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    except ValueError as e:
        msg = str(e)
        if "terminal state" in msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        if "Duplicate event_id" in msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)


@router.post(
    "/{session_id}/events/batch",
    response_model=List[IngestEventResponse],
    summary="Ingest a batch of agent events (up to 100)",
)
async def ingest_events_batch(
    session_id: str, request: IngestBatchRequest
) -> List[IngestEventResponse]:
    """Ingest multiple agent events sequentially in a single HTTP payload."""
    mgr = get_session_manager()
    try:
        return mgr.add_events_batch(session_id, request.events)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    except ValueError as e:
        msg = str(e)
        if "terminal state" in msg or "Duplicate event_id" in msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)


@router.post(
    "/{session_id}/finish",
    response_model=FinishSessionResponse,
    summary="Finish a live session and run diagnosis",
)
async def finish_session(
    session_id: str, request: Optional[FinishSessionRequest] = None
) -> FinishSessionResponse:
    """
    Finalize a live session.
    Triggers the grounded causal diagnosis pipeline asynchronously if requested.
    """
    mgr = get_session_manager()
    req = request or FinishSessionRequest()
    try:
        # Offload synchronous diagnosis execution to thread pool
        return await asyncio.to_thread(mgr.finish_session, session_id, req)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )


@router.post(
    "/{session_id}/diagnose",
    response_model=FullDiagnosisResponse,
    summary="Run on-demand diagnosis on active or completed session",
)
async def diagnose_session_endpoint(session_id: str) -> FullDiagnosisResponse:
    """Run mid-session or completed session diagnosis on-demand."""
    mgr = get_session_manager()
    try:
        return await asyncio.to_thread(mgr.diagnose_session, session_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/{session_id}/gnn-predict",
    summary="Run GNN Regression Intelligence prediction on live session graph",
)
async def gnn_predict_session_endpoint(session_id: str) -> Dict[str, Any]:
    """Runs Heterogeneous Graph Transformer (HGT) inference, vulnerability scoring, and GNNExplainer on live session."""
    mgr = get_session_manager()
    session = mgr.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    try:
        from session.converter import session_to_trace
        from regression.intelligence import run_gnn_regression_intelligence
    except ImportError:
        from backend.session.converter import session_to_trace
        from backend.regression.intelligence import run_gnn_regression_intelligence

    trace = session_to_trace(session)
    g = mgr.get_session_graph(session_id)
    diagnosis_res = session.diagnosis.diagnosis if session.diagnosis else None

    res = await asyncio.to_thread(run_gnn_regression_intelligence, trace, g, diagnosis_res)
    return res.model_dump()


@router.get(
    "",
    response_model=PaginatedSessions,
    summary="List session summaries",
)
@router.get(
    "/",
    response_model=PaginatedSessions,
    summary="List session summaries",
)
async def list_sessions(
    status_filter: Optional[SessionStatus] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> PaginatedSessions:
    """List session summaries with optional status filtering and pagination."""
    mgr = get_session_manager()
    summaries, total = mgr.list_sessions(status=status_filter, limit=limit, offset=offset)
    has_more = (offset + len(summaries)) < total
    return PaginatedSessions(
        items=summaries,
        total=total,
        limit=limit,
        offset=offset,
        has_more=has_more,
    )


@router.get(
    "/analytics",
    summary="Get aggregated system-wide agent reliability analytics",
)
async def get_analytics_summary() -> Dict[str, Any]:
    """
    Retrieve aggregated agent reliability analytics across all active and completed sessions.
    Includes failure taxonomy distribution, event volumes, and root-cause hotspots.
    """
    mgr = get_session_manager()
    return mgr.get_analytics_summary()


@router.get(
    "/{session_id}",
    response_model=TraceSession,
    summary="Get full session state",
)
async def get_session(session_id: str) -> TraceSession:
    """Retrieve full TraceSession detail by ID."""
    mgr = get_session_manager()
    session = mgr.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    return session


@router.get(
    "/{session_id}/graph",
    response_model=Dict[str, Any],
    summary="Get serialized NetworkX execution graph",
)
async def get_session_graph(session_id: str) -> Dict[str, Any]:
    """Retrieve serialized NetworkX execution graph matching AGENTS.md §10."""
    mgr = get_session_manager()
    session = mgr.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    g = mgr.get_graph(session_id)
    if not g:
        return {"nodes": [], "edges": []}

    root_cause_id = session.diagnosis.root_cause_node_id if session.diagnosis else ""
    evidence_ids = session.diagnosis.evidence_node_ids if session.diagnosis else []
    critical_path = session.full_diagnosis.critical_path if session.full_diagnosis else []

    return serialize_session_graph(
        g,
        root_cause_id=root_cause_id,
        evidence_ids=evidence_ids,
        critical_path=critical_path,
    )


@router.get(
    "/{session_id}/events",
    response_model=PaginatedEvents,
    summary="Get paginated list of session events",
)
async def list_session_events(
    session_id: str,
    event_type: Optional[EventType] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> PaginatedEvents:
    """Retrieve paginated events for a specific session."""
    mgr = get_session_manager()
    session = mgr.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    events = session.events
    if event_type:
        events = [e for e in events if e.event_type == event_type]

    total = len(events)
    page = events[offset : offset + limit]
    has_more = (offset + len(page)) < total

    return PaginatedEvents(
        items=page,
        total=total,
        limit=limit,
        offset=offset,
        has_more=has_more,
    )


@router.get(
    "/{session_id}/export-regression-test",
    summary="Export generated Pytest regression test file script",
)
async def export_regression_test(session_id: str) -> Dict[str, Any]:
    """
    Fulfills FR-18: Export standalone Pytest regression test script based on session diagnosis.
    Connects Person 2's Regression Generator to the core system.
    """
    mgr = get_session_manager()
    session = mgr.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    try:
        from agent365.engine.regression import generate_pytest_regression_script
        full_diag = session.full_diagnosis
        if not full_diag:
            full_diag = mgr.diagnose_session(session_id)

        spans_data = [
            {
                "trace_id": session_id,
                "span_id": e.event_id,
                "name": e.content[:30] if e.content else e.event_type.value,
                "kind": "TOOL" if "tool" in e.event_type.value else "CHAIN",
                "status_code": "ERROR" if e.event_type.value == "error" else "OK",
                "attributes": {
                    "input.value": session.description or session.name,
                    "tool.name": e.metadata.get("tool_name", e.event_type.value),
                    "output.value": e.content,
                },
            }
            for e in session.events
        ]
        script_code = generate_pytest_regression_script(full_diag, spans_data)
        return {
            "session_id": session_id,
            "filename": f"test_regression_{session_id[:8]}.py",
            "pytest_code": script_code,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate regression test script: {str(e)}",
        )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a session",
)
async def delete_session(session_id: str):
    """Delete a session and clear its graph resources."""
    mgr = get_session_manager()
    deleted = mgr.delete_session(session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.websocket("/ws/{session_id}")
@router.websocket("/{session_id}/ws")
async def websocket_session_stream(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time live trace session event streaming.
    Pushes node additions, edge additions, anomaly flags, and diagnosis completion.
    """
    mgr = get_session_manager()
    session = mgr.get_session(session_id)
    if not session:
        await websocket.close(code=4004, reason=f"Session '{session_id}' not found.")
        return

    await ws_hub.connect(session_id, websocket)
    try:
        # Send initial connection acknowledgment with current session status
        await websocket.send_json(
            {
                "type": "connected",
                "session_id": session_id,
                "status": session.status.value,
                "event_count": session.event_count,
            }
        )

        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type") if isinstance(data, dict) else None

            if msg_type == "request_snapshot":
                graph_payload = await get_session_graph(session_id)
                await websocket.send_json(
                    {
                        "type": "snapshot",
                        "session_id": session_id,
                        "graph": graph_payload,
                    }
                )
            elif msg_type == "pong":
                pass
    except WebSocketDisconnect:
        await ws_hub.disconnect(session_id, websocket)
    except Exception:
        await ws_hub.disconnect(session_id, websocket)
