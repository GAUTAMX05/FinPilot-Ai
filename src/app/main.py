import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from src.app.core.config import settings
from src.app.api import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("FinPilotAIApp")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="FinPilot AI — Autonomous Multi-Agent Financial Digital Twin & Decision Operating System for enterprise finance, invoice auditing, budget governance, and cash forecasting.",
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


@app.get("/logo.png", tags=["Assets"])
@app.get("/favicon.ico", tags=["Assets"])
def serve_logo():
    logo_path = os.path.join(STATIC_DIR, "assets", "logo.png")
    if os.path.exists(logo_path):
        return FileResponse(logo_path, media_type="image/png")
    return HTMLResponse(status_code=404, content="Logo not found")


@app.get("/health", tags=["System Health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "governance_threshold_inr": settings.HITL_APPROVAL_THRESHOLD_INR,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.app.main:app", host="0.0.0.0", port=8000, reload=True)
