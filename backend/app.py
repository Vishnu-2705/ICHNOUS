"""
TraceMind Backend FastAPI Application Entrypoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from routes.traces import router as traces_router
except ImportError:
    from backend.routes.traces import router as traces_router

app = FastAPI(
    title="TraceMind Backend",
    description="Backend services for TraceMind AI Reliability OS",
    version="0.1.0",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(traces_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "TraceMind Backend"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
