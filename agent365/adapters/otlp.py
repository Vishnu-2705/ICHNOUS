"""
OTLP File and Dictionary Adapter for Agent 365.

Reads standard OTLP (OpenTelemetry Protocol) JSON trace files or raw dictionary payloads.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Union

from agent365.otel.models import OTelSpan


def load_otlp_trace_from_file(file_path: Union[str, Path]) -> List[OTelSpan]:
    """
    Load OTLP JSON trace file and parse into a list of OTelSpan objects.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"OTLP trace file not found: {file_path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        spans_raw = data.get("spans", data.get("resourceSpans", []))
        if not spans_raw and "span_id" in data:
            spans_raw = [data]
    elif isinstance(data, list):
        spans_raw = data
    else:
        spans_raw = []

    return [OTelSpan.from_otlp_dict(s) for s in spans_raw]
