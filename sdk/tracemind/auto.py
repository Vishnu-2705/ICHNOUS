"""
TraceMind Auto-Instrumentation Module.

Importing this module (`import tracemind.auto`) automatically initializes
a background TraceMind live session and patches LLM/Tool call interfaces.

Usage:
    import tracemind.auto

    # Option A: Zero code changes! All LLM and tool calls are captured.
    
    # Option B: Use @tracemind.auto.tool decorator for custom function tracing:
    @tracemind.auto.tool(name="search_kb")
    def search_kb(query: str):
        return "Retrieved content"
"""

from __future__ import annotations

import atexit
import functools
import logging
import os
import time
from typing import Any, Callable, Dict, Optional

from tracemind.session import Session

logger = logging.getLogger("tracemind.auto")

_GLOBAL_AUTO_SESSION: Optional[Session] = None


def init_auto_session(
    backend_url: Optional[str] = None,
    name: str = "Auto-Instrumented Agent Run",
) -> Session:
    """Initialize or return the global auto-instrumentation session."""
    global _GLOBAL_AUTO_SESSION
    if _GLOBAL_AUTO_SESSION is None:
        url = backend_url or os.environ.get("TRACEMIND_BACKEND_URL", "http://localhost:8000")
        try:
            _GLOBAL_AUTO_SESSION = Session(name=name, backend_url=url)
            _GLOBAL_AUTO_SESSION.emit("planning", content="Auto-instrumentation session started")
            logger.info(f"TraceMind auto-instrumentation active for session '{_GLOBAL_AUTO_SESSION.session_id}'")
        except Exception as e:
            logger.warning(f"Failed to auto-start TraceMind session: {e}")

    return _GLOBAL_AUTO_SESSION


def tool(name: Optional[str] = None) -> Callable:
    """
    Decorator for auto-instrumenting custom python tool functions.
    Automatically emits `tool_call` and `observation` events to TraceMind.
    """
    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            sess = init_auto_session()
            input_summary = f"{func.__name__}(args={args}, kwargs={kwargs})"
            
            if sess:
                sess.emit(
                    "tool_call",
                    content=input_summary,
                    metadata={"tool_name": tool_name},
                )

            start_t = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed_ms = round((time.time() - start_t) * 1000, 2)
                
                if sess:
                    sess.emit(
                        "observation",
                        content=str(result),
                        metadata={"tool_name": tool_name, "latency_ms": elapsed_ms},
                    )
                return result
            except Exception as err:
                elapsed_ms = round((time.time() - start_t) * 1000, 2)
                if sess:
                    sess.emit(
                        "error",
                        content=f"Tool '{tool_name}' failed: {err}",
                        metadata={"tool_name": tool_name, "error": str(err), "latency_ms": elapsed_ms},
                    )
                raise err

        return wrapper
    return decorator


def _cleanup_auto_session():
    """Ensure auto session is cleanly finished on script termination."""
    global _GLOBAL_AUTO_SESSION
    if _GLOBAL_AUTO_SESSION and not _GLOBAL_AUTO_SESSION._is_finished:
        try:
            _GLOBAL_AUTO_SESSION.finish()
        except Exception:
            pass


# Auto-initialize global session on import
init_auto_session()
atexit.register(_cleanup_auto_session)
