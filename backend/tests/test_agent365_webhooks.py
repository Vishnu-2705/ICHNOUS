"""
Unit tests for Agent 365 Slack & GitHub PR Webhook Adapters.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Ensure sys.path includes backend and project root
backend_dir = Path(__file__).resolve().parent.parent
project_dir = backend_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

from agent365.adapters.webhooks import post_github_pr_comment, post_to_slack
from agent365.engine.analyzer import analyze_otel_trace


class TestAgent365Webhooks:
    def test_post_to_slack_mocked(self):
        otel_spans = [
            {"span_id": "s1", "trace_id": "t1", "name": "plan", "attributes": {"openinference.span.kind": "AGENT"}},
            {
                "span_id": "s2",
                "parent_span_id": "s1",
                "trace_id": "t1",
                "name": "search_knowledge_base",
                "attributes": {
                    "openinference.span.kind": "TOOL",
                    "tool.name": "search_knowledge_base",
                    "retrieval.relevance_score": 0.3,
                    "note": "stale doc",
                },
            },
            {"span_id": "s3", "parent_span_id": "s2", "trace_id": "t1", "name": "final_answer", "attributes": {"openinference.span.kind": "CHAIN"}},
        ]
        diagnosis = analyze_otel_trace(otel_spans)

        mock_post = MagicMock()
        mock_post.status_code = 200

        with patch("requests.post", return_value=mock_post):
            ok = post_to_slack("https://hooks.slack.com/services/mock", diagnosis)
            assert ok is True

    def test_post_github_pr_comment_mocked(self):
        otel_spans = [
            {"span_id": "s1", "trace_id": "t1", "name": "plan", "attributes": {"openinference.span.kind": "AGENT"}},
            {
                "span_id": "s2",
                "parent_span_id": "s1",
                "trace_id": "t1",
                "name": "search_knowledge_base",
                "attributes": {
                    "openinference.span.kind": "TOOL",
                    "tool.name": "search_knowledge_base",
                    "retrieval.relevance_score": 0.3,
                    "note": "stale doc",
                },
            },
            {"span_id": "s3", "parent_span_id": "s2", "trace_id": "t1", "name": "final_answer", "attributes": {"openinference.span.kind": "CHAIN"}},
        ]
        diagnosis = analyze_otel_trace(otel_spans)

        mock_post = MagicMock()
        mock_post.status_code = 201

        with patch("requests.post", return_value=mock_post):
            ok = post_github_pr_comment("owner/repo", 42, "ghp_mock_token", diagnosis)
            assert ok is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
