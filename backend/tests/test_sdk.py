"""
Unit and Integration tests for the TraceMind Python SDK.

Tests:
- Synchronous Session lifecycle with TestClient
- Auto-linking logic in SDK
- Context manager exception handling and emit_error
- Asynchronous AsyncSession client
- Full E2E run: SDK -> SessionManager -> Diagnosis
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
import pytest

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Ensure sdk directory is in sys.path
sdk_dir = backend_dir.parent / "sdk"
if str(sdk_dir) not in sys.path:
    sys.path.insert(0, str(sdk_dir))

from app import app
from routes.sessions import session_manager
from tracemind.exceptions import ConnectionError, SessionError, ValidationError
from tracemind.models import EventType
from tracemind.session import Session

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_sessions():
    """Clear session storage before each test."""
    session_manager.storage.clear()
    session_manager._graphs.clear()


class TestSDKClient:
    def test_session_init_and_start(self):
        """Test SDK Session initialization sending POST /sessions/start."""
        def mock_post(url, json=None, headers=None, timeout=10):
            res = client.post("/sessions/start", json=json)
            mock_res = MagicMock()
            mock_res.status_code = res.status_code
            mock_res.json = lambda: res.json()
            mock_res.text = res.text
            return mock_res

        with patch("requests.post", side_effect=mock_post):
            session = Session(name="SDK Test Run", description="SDK unit test")
            assert session.session_id is not None
            assert "/ws/sessions/" in session.ws_url

    def test_session_emit_events(self):
        """Test SDK Session emitting events sequentially."""
        def mock_post(url, json=None, headers=None, timeout=10):
            path = url.replace("http://localhost:8000", "")
            res = client.post(path, json=json)
            mock_res = MagicMock()
            mock_res.status_code = res.status_code
            mock_res.json = lambda: res.json()
            mock_res.text = res.text
            return mock_res

        with patch("requests.post", side_effect=mock_post):
            session = Session(name="SDK Emit Test")
            e1 = session.emit("planning", content="Plan")
            e2 = session.emit("tool_call", content="Tool", metadata={"tool_name": "search"})
            e3 = session.emit("final_answer", content="Done")

            assert e1 == "evt_1"
            assert e2 == "evt_2"
            assert e3 == "evt_3"

    def test_session_context_manager_e2e_retrieval(self):
        """Test SDK context manager emitting a full retrieval failure trace and diagnosing."""
        def mock_post(url, json=None, headers=None, timeout=30):
            path = url.replace("http://localhost:8000", "")
            res = client.post(path, json=json)
            mock_res = MagicMock()
            mock_res.status_code = res.status_code
            mock_res.json = lambda: res.json()
            mock_res.text = res.text
            return mock_res

        with patch("requests.post", side_effect=mock_post):
            with Session(name="SDK Retrieval Test") as s:
                s.emit("planning", content="Refund query")
                s.emit(
                    "tool_call",
                    content="search_kb()",
                    metadata={"tool_name": "search_knowledge_base", "relevance_score": 0.4},
                )
                s.emit("observation", content="Retrieved stale policy 2023")
                s.emit("final_answer", content="Deny refund")

            sid = s.session_id
            db_session = session_manager.get_session(sid)
            assert db_session.status.value == "completed"
            assert db_session.diagnosis is not None
            assert db_session.diagnosis.failure_category == "Retrieval"

    def test_session_context_manager_captures_exception(self):
        """Test SDK context manager emits error event on unhandled exception."""
        def mock_post(url, json=None, headers=None, timeout=30):
            path = url.replace("http://localhost:8000", "")
            res = client.post(path, json=json)
            mock_res = MagicMock()
            mock_res.status_code = res.status_code
            mock_res.json = lambda: res.json()
            mock_res.text = res.text
            return mock_res

        with pytest.raises(ZeroDivisionError):
            with patch("requests.post", side_effect=mock_post):
                with Session(name="SDK Exception Test") as s:
                    s.emit("planning", content="Start")
                    _ = 1 / 0

        sid = s.session_id
        db_session = session_manager.get_session(sid)
        assert db_session.event_count == 2
        assert db_session.events[1].event_type.value == "error"
        assert "ZeroDivisionError" in db_session.events[1].metadata.get("exception_type", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
