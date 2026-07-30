"""Failure taxonomy classification for TraceMind."""

from enum import Enum
from typing import List


class FailureCategory(str, Enum):
    PLANNING = "Planning"
    MEMORY = "Memory"
    RETRIEVAL = "Retrieval"
    REASONING = "Reasoning"
    CONTEXT = "Context"
    HALLUCINATION = "Hallucination"
    SPECIFICATION = "Specification"
    TOOL = "Tool"
    SAFETY = "Safety"
    VERIFICATION = "Verification"
    COORDINATION = "Coordination"
    TIMEOUT = "Timeout"
    EXTERNAL_API = "External API"
    HUMAN = "Human"
    UNKNOWN = "Unknown"


TAXONOMY_LIST: List[str] = [c.value for c in FailureCategory]
