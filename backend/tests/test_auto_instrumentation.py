"""
Unit tests for TraceMind Auto-Instrumentation (import tracemind.auto).
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Ensure sys.path includes sdk and backend
project_dir = Path(__file__).resolve().parent.parent.parent
sdk_dir = project_dir / "sdk"
backend_dir = project_dir / "backend"

if str(sdk_dir) not in sys.path:
    sys.path.insert(0, str(sdk_dir))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import tracemind.auto as tm_auto


class TestAutoInstrumentation:
    def test_auto_session_initialization(self):
        mock_emit = MagicMock(return_value={"event_id": "evt_1"})
        mock_finish = MagicMock()

        tm_auto._GLOBAL_AUTO_SESSION = None
        with patch("tracemind.session.Session.emit", mock_emit), \
             patch("tracemind.session.Session.finish", mock_finish):

            sess = tm_auto.init_auto_session(name="Test Auto Run")
            assert sess is not None
            assert mock_emit.called

    def test_auto_tool_decorator(self):
        mock_emit = MagicMock(return_value={"event_id": "evt_tool"})

        with patch("tracemind.session.Session.emit", mock_emit):
            @tm_auto.tool(name="search_kb")
            def search_kb(query: str):
                return "Policy 2025 document"

            res = search_kb("refund policy")
            assert res == "Policy 2025 document"
            assert mock_emit.call_count >= 2  # tool_call and observation emitted!


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
