"""Trace Mind Fixtures Package & Helpers."""

import json
from pathlib import Path
from typing import Dict

try:
    from models.trace import Trace
except ImportError:
    from backend.models.trace import Trace

FIXTURES_DIR = Path(__file__).resolve().parent


def load_fixture_json(name_or_key: str) -> dict:
    """
    Load a trace fixture as a raw dictionary from its JSON file.
    Accepts keys like 'retrieval', 'trace_retrieval', or 'retrieval_failure.json'.
    """
    filename = name_or_key
    if not filename.endswith(".json"):
        if filename.startswith("trace_"):
            filename = filename.replace("trace_", "") + "_failure.json"
        elif not filename.endswith("_failure"):
            filename = f"{filename}_failure.json"
        else:
            filename = f"{filename}.json"

    file_path = FIXTURES_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Fixture file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_fixture_trace(name_or_key: str) -> Trace:
    """
    Load a trace fixture as a validated Pydantic Trace model.
    """
    data = load_fixture_json(name_or_key)
    return Trace.model_validate(data)


def get_retrieval_failure_trace() -> Trace:
    """Return validated Retrieval Failure trace."""
    return load_fixture_trace("retrieval_failure.json")


def get_tool_failure_trace() -> Trace:
    """Return validated Tool Failure trace."""
    return load_fixture_trace("tool_failure.json")


def get_coordination_failure_trace() -> Trace:
    """Return validated Coordination Failure trace."""
    return load_fixture_trace("coordination_failure.json")


def get_all_fixtures() -> Dict[str, Trace]:
    """Return a dictionary of all available trace fixtures."""
    return {
        "trace_retrieval": get_retrieval_failure_trace(),
        "trace_tool": get_tool_failure_trace(),
        "trace_coordination": get_coordination_failure_trace(),
    }


__all__ = [
    "load_fixture_json",
    "load_fixture_trace",
    "get_retrieval_failure_trace",
    "get_tool_failure_trace",
    "get_coordination_failure_trace",
    "get_all_fixtures",
]
