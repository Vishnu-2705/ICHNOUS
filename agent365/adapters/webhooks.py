"""
Slack & GitHub PR Webhook Adapter for Agent 365.

Formats and dispatches causal root-cause notifications and git diff patches to:
1. Slack Webhooks
2. GitHub Actions / PR Comments
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
import requests

try:
    from models.trace import FullDiagnosisResponse
except ImportError:
    from backend.models.trace import FullDiagnosisResponse

logger = logging.getLogger("agent365.webhooks")


def post_to_slack(webhook_url: str, diagnosis: FullDiagnosisResponse) -> bool:
    """
    Format and post a causal diagnosis result to a Slack Incoming Webhook.
    """
    diag = diagnosis.diagnosis
    category_emoji = {
        "Retrieval": "🔍",
        "Tool": "🛠️",
        "Coordination": "🔄",
    }.get(diag.failure_category, "⚠️")

    payload = {
        "text": f"{category_emoji} *Agent 365 Causal Failure Alert*",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Agent 365 Causal Failure Alert* {category_emoji}\n"
                        f"*Failure Category:* `{diag.failure_category}`\n"
                        f"*Root Cause Node:* `{diag.root_cause_node_id}`\n"
                        f"*Confidence:* `{diag.confidence:.0%}`"
                    ),
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Explanation:*\n>{diag.explanation}",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Suggested Patch Target:* `{diag.suggested_fix.target}`\n```\n{diag.suggested_fix.diff}\n```",
                },
            },
        ],
    }

    try:
        resp = requests.post(webhook_url, json=payload, headers={"Content-Type": "application/json"}, timeout=5)
        return resp.status_code == 200
    except requests.RequestException as e:
        logger.warning(f"Failed to post Slack notification: {e}")
        return False


def post_github_pr_comment(
    repo: str,
    pr_number: int,
    github_token: str,
    diagnosis: FullDiagnosisResponse,
) -> bool:
    """
    Post a markdown-formatted causal diagnosis comment to a GitHub PR.
    """
    diag = diagnosis.diagnosis
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"

    comment_body = f"""### 🧠 Agent 365 Causal Failure Diagnosis

| Metric | Value |
|---|---|
| **Failure Category** | `{diag.failure_category}` |
| **Root Cause Span ID** | `{diag.root_cause_node_id}` |
| **Confidence Score** | `{diag.confidence:.0%}` |
| **Grounded** | `{diag.grounded}` |

#### 📝 Explanation
> {diag.explanation}

#### 🛠️ Suggested Code / Prompt Patch (`{diag.suggested_fix.target}`)
```diff
{diag.suggested_fix.diff}
```
"""

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        resp = requests.post(url, json={"body": comment_body}, headers=headers, timeout=10)
        return resp.status_code in (200, 201)
    except requests.RequestException as e:
        logger.warning(f"Failed to post GitHub PR comment: {e}")
        return False
