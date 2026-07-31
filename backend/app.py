"""
TraceMind Backend FastAPI Application Entrypoint.
"""

from datetime import datetime, timezone
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
project_dir = backend_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

from config import settings
from routes.sessions import router as sessions_router, session_manager, ws_hub
from routes.traces import router as traces_router
from routes.upload import router as upload_router
from agent365.api import router as agent365_router

START_TIME = datetime.now(timezone.utc)

app = FastAPI(
    title="TraceMind & Agent 365 Backend",
    description="Backend services for TraceMind Live Agent Reliability OS & Agent 365 OTel Engine",
    version="0.3.0",
)

# Enable CORS based on settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(traces_router)
app.include_router(sessions_router)
app.include_router(upload_router)
app.include_router(agent365_router)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root landing page with API summary, documentation links, and endpoint index."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TraceMind Backend Service</title>
        <style>
            body { font-family: system-ui, -apple-system, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 2rem; }
            .card { max-width: 800px; margin: 2rem auto; background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 2rem; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5); }
            h1 { color: #f59e0b; margin-top: 0; font-size: 1.8rem; display: flex; items-center; gap: 0.5rem; }
            p { color: #94a3b8; line-height: 1.6; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-top: 1.5rem; }
            .endpoint { background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 1rem; text-decoration: none; color: #e2e8f0; transition: border-color 0.2s; }
            .endpoint:hover { border-color: #f59e0b; }
            .endpoint h3 { margin: 0 0 0.5rem 0; font-size: 1rem; color: #38bdf8; }
            .endpoint p { margin: 0; font-size: 0.85rem; color: #64748b; }
            .badge { display: inline-block; background: #059669; color: #ecfdf5; font-size: 0.75rem; font-weight: bold; padding: 0.2rem 0.6rem; border-radius: 9999px; margin-left: auto; }
        </style>
    </head>
    <body>
        <div class="card">
            <div style="display:flex; align-items:center;">
                <h1>🧠 TraceMind Backend</h1>
                <span class="badge">v0.2.0 LIVE</span>
            </div>
            <p>The Causal Debugger for Autonomous AI Systems — Live Agent Runtime & Ingestion Engine.</p>
            
            <h2>Explore API Endpoints</h2>
            <div class="grid">
                <a href="/docs" class="endpoint">
                    <h3>📚 Interactive API Docs</h3>
                    <p>Swagger UI documentation & manual request testing</p>
                </a>
                <a href="/health" class="endpoint">
                    <h3>💚 /health</h3>
                    <p>System metrics, uptime, active WebSocket connections</p>
                </a>
                <a href="/sessions" class="endpoint">
                    <h3>🔴 /sessions</h3>
                    <p>Live agent sessions catalog & execution state</p>
                </a>
                <a href="/traces" class="endpoint">
                    <h3>📁 /traces</h3>
                    <p>Static fixture catalog & baseline replay traces</p>
                </a>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)


@app.get("/health")
async def health_check():
    """Enhanced health check endpoint returning service status, metrics, and uptime."""
    uptime_sec = (datetime.now(timezone.utc) - START_TIME).total_seconds()
    metrics = session_manager.get_metrics()
    return {
        "status": "healthy",
        "service": "TraceMind Backend",
        "version": "0.2.0",
        "llm_configured": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "uptime_seconds": round(uptime_sec, 2),
        "websocket_connections": ws_hub.connection_count(),
        "metrics": metrics,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host=settings.host, port=settings.port, reload=True)
