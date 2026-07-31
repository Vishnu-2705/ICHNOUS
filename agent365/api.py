"""
FastAPI REST Router for Agent 365.

Exposes REST endpoints for OpenTelemetry trace analysis:
- `POST /agent365/diagnose` -> Ingest OTel JSON spans and return FullDiagnosisResponse
- `POST /agent365/phoenix/diagnose` -> Fetch trace from Arize Phoenix, diagnose, annotate, and return response
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

try:
    from models.trace import FullDiagnosisResponse
except ImportError:
    from backend.models.trace import FullDiagnosisResponse

from agent365.adapters.phoenix import PhoenixAdapter
from agent365.engine.analyzer import analyze_otel_trace
from agent365.otel.models import OTelSpan

router = APIRouter(prefix="/agent365", tags=["Agent 365 OTel Causal Engine"])


class OTelDiagnoseRequest(BaseModel):
    """Payload for directly submitting OTel spans for causal diagnosis."""

    spans: List[Dict[str, Any]] = Field(..., description="List of OTLP / OpenInference span dictionaries")


class PhoenixDiagnoseRequest(BaseModel):
    """Payload for triggering Arize Phoenix trace diagnosis."""

    phoenix_url: str = Field(default="http://localhost:6006", description="Arize Phoenix server URL")
    trace_id: str = Field(..., description="Phoenix trace ID to fetch and diagnose")
    annotate: bool = Field(default=True, description="Post root-cause annotation back to Phoenix")


@router.post(
    "/diagnose",
    response_model=FullDiagnosisResponse,
    status_code=status.HTTP_200_OK,
    summary="Run causal diagnosis on OpenTelemetry GenAI spans",
)
async def diagnose_otel_spans(request: OTelDiagnoseRequest) -> FullDiagnosisResponse:
    """Analyze OpenTelemetry / OpenInference spans and return causal root-cause diagnosis."""
    if not request.spans:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The 'spans' list must contain at least one OpenTelemetry span.",
        )
    try:
        return analyze_otel_trace(request.spans)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/phoenix/diagnose",
    response_model=FullDiagnosisResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch trace from Arize Phoenix, run causal diagnosis, and write span annotation",
)
async def diagnose_phoenix_trace(request: PhoenixDiagnoseRequest) -> FullDiagnosisResponse:
    """Fetch live trace from Arize Phoenix, compute causal root-cause, and annotate span."""
    adapter = PhoenixAdapter(phoenix_url=request.phoenix_url)
    try:
        spans = adapter.fetch_trace_spans(request.trace_id)
        result = analyze_otel_trace(spans)

        if request.annotate:
            adapter.annotate_root_cause(
                trace_id=request.trace_id,
                span_id=result.diagnosis.root_cause_node_id,
                failure_category=result.diagnosis.failure_category,
                confidence=result.diagnosis.confidence,
                explanation=result.diagnosis.explanation,
            )

        return result
    except ConnectionError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
