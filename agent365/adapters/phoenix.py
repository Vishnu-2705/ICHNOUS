"""
Arize Phoenix REST API Adapter for Agent 365.

Enables Agent 365 to:
1. Fetch live OTel trace trees from a self-hosted Arize Phoenix server (`GET /v1/traces/{id}`)
2. Write causal root-cause annotations and confidence scores back onto Phoenix spans (`POST /v1/span_annotations`)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import requests

from agent365.otel.models import OTelSpan

logger = logging.getLogger("agent365.phoenix")


class PhoenixAdapter:
    """
    Adapter for communicating with Arize Phoenix (Apache 2.0) self-hosted trace store.
    """

    def __init__(self, phoenix_url: str = "http://localhost:6006") -> None:
        self.phoenix_url = phoenix_url.rstrip("/")

    def fetch_trace_spans(self, trace_id: str) -> List[OTelSpan]:
        """
        Fetch all spans belonging to a trace_id from Arize Phoenix.
        """
        url = f"{self.phoenix_url}/v1/traces/{trace_id}"
        try:
            resp = requests.get(url, headers={"Accept": "application/json"}, timeout=10)
        except requests.RequestException as e:
            raise ConnectionError(
                f"Could not connect to Arize Phoenix server at '{url}': {e}"
            ) from e

        if resp.status_code != 200:
            raise ValueError(
                f"Failed to fetch trace '{trace_id}' from Phoenix (HTTP {resp.status_code}): {resp.text}"
            )

        data = resp.json()
        raw_spans = data.get("spans", data if isinstance(data, list) else [])
        return [OTelSpan.from_otlp_dict(s) for s in raw_spans]

    def annotate_root_cause(
        self,
        trace_id: str,
        span_id: str,
        failure_category: str,
        confidence: float,
        explanation: str,
    ) -> bool:
        """
        Post a causal root-cause annotation back to Arize Phoenix.
        """
        url = f"{self.phoenix_url}/v1/span_annotations"
        payload = {
            "span_id": span_id,
            "name": "agent365.root_cause",
            "annotator_kind": "AGENT_365_CAUSAL_ENGINE",
            "label": failure_category,
            "score": confidence,
            "explanation": explanation,
            "metadata": {
                "trace_id": trace_id,
                "diagnosed_by": "Agent 365 OTel Engine",
            },
        }

        try:
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
            return resp.status_code in (200, 201)
        except requests.RequestException as e:
            logger.warning(f"Failed to write annotation to Phoenix: {e}")
            return False
