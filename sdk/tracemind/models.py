"""
Data models for the TraceMind Python SDK.
"""

from enum import Enum
from typing import Any, Dict, List, Optional


class EventType(str, Enum):
    """Supported agent lifecycle event types."""

    PLANNING = "planning"
    LLM_CALL = "llm_call"
    LLM_RESPONSE = "llm_response"
    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"
    OBSERVATION = "observation"
    REASONING = "reasoning"
    DECISION = "decision"
    DELEGATION = "delegation"
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    ERROR = "error"
    FINAL_ANSWER = "final_answer"
    CUSTOM = "custom"
