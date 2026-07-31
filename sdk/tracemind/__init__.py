"""
TraceMind Python SDK — Real-Time AI Agent Runtime Instrumentation.

Usage:
    import tracemind as tm

    with tm.Session(name="Support Agent Run") as session:
        session.emit("planning", content="Analyzing query...")
        session.emit("tool_call", content="search_kb(query='refund')")
        session.emit("final_answer", content="Refund granted.")
"""

from tracemind.async_session import AsyncSession
from tracemind.exceptions import (
    ConnectionError,
    SessionError,
    TraceMindError,
    ValidationError,
)
from tracemind.models import EventType
from tracemind.session import Session

__version__ = "0.2.0"

__all__ = [
    "Session",
    "AsyncSession",
    "EventType",
    "TraceMindError",
    "ConnectionError",
    "SessionError",
    "ValidationError",
    "__version__",
]
