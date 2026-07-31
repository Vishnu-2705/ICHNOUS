"""
TraceMind Configuration Settings.

Loads system configuration from environment variables with sensible defaults.
"""

import os
from typing import List
from pydantic import BaseModel


# Load .env if present
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()


class Settings(BaseModel):
    """Application settings and configuration."""

    host: str = os.environ.get("TRACEMIND_HOST", "0.0.0.0")
    port: int = int(os.environ.get("TRACEMIND_PORT", "8000"))
    api_key: str = os.environ.get("TRACEMIND_API_KEY", "")
    cors_origins: List[str] = [
        origin.strip()
        for origin in os.environ.get(
            "TRACEMIND_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,*"
        ).split(",")
    ]
    max_sessions: int = int(os.environ.get("TRACEMIND_MAX_SESSIONS", "100"))
    session_ttl_seconds: int = int(os.environ.get("TRACEMIND_SESSION_TTL", "3600"))
    llm_api_key_set: bool = bool(
        os.environ.get("NVIDIA_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY")
    )


settings = Settings()
