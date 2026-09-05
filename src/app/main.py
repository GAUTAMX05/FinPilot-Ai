# -*- coding: utf-8 -*-
import os
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from src.app.core.config import settings
from src.app.core.database import init_db, get_db_connection, get_db_stats
from src.app.services.llm_provider import llm_status
from src.app.services.razorpay_service import razorpay_service
from src.app.api import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("FinPilotAIApp")

# Ensure SQLite schema and initial benchmark data are bootstrap ready
init_db()

app = FastAPI(
    title="FinPilot AI — Autonomous Finance Controller for Razorpay Merchants",
    version=settings.VERSION,
    description="Autonomous Finance Controller closing the loop across Razorpay payments, settlements, invoices, 3-way deterministic reconciliation, AI root-cause analysis, and human-in-the-loop approvals.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Cross-Origin Resource Sharing (CORS)
# Note: allow_credentials=True is invalid with allow_origins=["*"] in browsers.
# Use CORS_ORIGINS env (comma-separated) in production, e.g. your frontend domain.
_cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
_allow_credentials = False if _cors_origins == ["*"] else True
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Static UI Dashboard
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    js_dir = os.path.join(STATIC_DIR, "js")
    if os.path.exists(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")
    assets_dir = os.path.join(STATIC_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


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


@app.get("/health", tags=["Health & Observability"])
def health_check():
    """Liveness probe reporting service status and runtime version."""
    return {
        "status": "healthy",
        "app": "FinPilot AI — Autonomous Finance Controller for Razorpay Merchants",
        "version": settings.VERSION,
        "build": os.getenv("RENDER_GIT_COMMIT", "")[:7] or "local",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/ready", tags=["Health & Observability"])
def readiness_check():
    """
    Readiness probe validating database connectivity, benchmark dataset integrity,
    AI provider status, and gateway status without leaking credentials.
    """
    try:
        db_stats = get_db_stats()
        gw_status = razorpay_service.get_gateway_status()
        ai = llm_status()

        return {
            "status": "ready" if db_stats.get("connected") else "degraded",
            "app": "FinPilot AI — Autonomous Finance Controller",
            "database": db_stats,
            "ai": {"ai_ready": ai.get("ai_ready"), "provider": ai.get("supervisor", {}).get("provider"),
                   "model": ai.get("supervisor", {}).get("model")},
            "gateway": {
                "mode": gw_status["gateway_mode"],
                "is_configured": gw_status["is_configured"],
                "supported_currencies": gw_status["supported_currencies"]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"[ReadinessCheck] Service not ready: {e}")
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("src.app.main:app", host="0.0.0.0", port=port, reload=False)
