# -*- coding: utf-8 -*-
"""AI + DB readiness status (safe: no secrets)."""
import os
from fastapi import APIRouter
from src.app.services.llm_provider import llm_status
from src.app.core.database import get_db_stats
from src.app.services.razorpay_service import razorpay_service

router = APIRouter()


@router.get("/ai/status", tags=["Health & Observability"])
def ai_status():
    """Which LLM provider is active (OpenAI/OpenCode/Groq/Anthropic/simulation)."""
    status = llm_status()
    status["build"] = os.getenv("RENDER_GIT_COMMIT", "")[:7] or "local"
    return status


@router.get("/db/status", tags=["Health & Observability"])
def db_status():
    """Database engine + seed counts (Postgres vs SQLite)."""
    stats = get_db_stats()
    return {"status": "ready" if stats.get("connected") else "degraded", **stats}


@router.get("/gateway-status", tags=["Health & Observability"])
def gateway_status_compat():
    """Alias without leaking secrets (same as controller gateway-status)."""
    return razorpay_service.get_gateway_status()
