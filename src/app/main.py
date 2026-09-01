import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from src.app.core.config import settings
from src.app.core.database import init_db
from src.app.api import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("FinPilotAIApp")

# Ensure SQLite schema and initial data are ready
init_db()

app = FastAPI(
    title="FinPilot AI — Autonomous Finance Controller for Razorpay Merchants",
    version=settings.VERSION,
    description="Autonomous Finance Controller closing the loop across Razorpay payments, settlements, invoices, 3-way deterministic reconciliation, AI root-cause analysis, and human-in-the-loop approvals.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Static UI Dashboard
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse, tags=["Dashboard UI"])
@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard UI"])
def serve_dashboard():
    """Serves the rich, responsive AI Finance Controller web dashboard."""
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(
            content=content,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )
    return HTMLResponse("<h1>FinPilot AI API is running. Access <a href='/docs'>/docs</a> for Swagger UI.</h1>")


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint for Render/container readiness."""
    return {
        "status": "healthy",
        "app": "FinPilot AI — Autonomous Finance Controller for Razorpay Merchants",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("src.app.main:app", host="0.0.0.0", port=port, reload=False)
