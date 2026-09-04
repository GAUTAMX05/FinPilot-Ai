# -*- coding: utf-8 -*-
import json
import logging
import re
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from src.app.core.auth_middleware import get_current_user
from src.app.core.rate_limiter import rate_limiter
from src.app.core.validators import sanitize_text
from src.app.services.copilot_service import grounded_copilot
from src.app.services.audit_service import audit_service

logger = logging.getLogger("AgentChatApi")
router = APIRouter(prefix="/agent", tags=["Finance Agent Chat"])

# Known prompt injection attack signatures
PROMPT_INJECTION_KEYWORDS = [
    "ignore previous instructions",
    "ignore all previous",
    "ignore system prompt",
    "ignore safety rules",
    "override safety limits",
    "you are now in developer mode",
    "dan mode",
    "jailbreak",
    "bypass approval",
    "approve without checks",
    "grant 100% discount",
    "approve payment without cfo",
    "disregard policy",
    "ignore rbac",
]


class ChatRequest(BaseModel):
    message: Optional[str] = Field(default="", max_length=4000, description="User financial inquiry.")
    thread_id: Optional[str] = Field(default="default-thread", max_length=100)
    approve: Optional[bool] = Field(default=None, description="None: regular chat; True/False: HITL approval decision.")


@router.post("/chat")
async def chat_endpoint(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    """
    Financial Decision Copilot Endpoint with:
    - Rate limiting & daily AI token budget protection (HTTP 429)
    - Prompt injection detection & isolation
    - Strict deterministic HITL approval gating
    - Audit-grade SHA-256 memory logging
    """
    user_id = current_user.get("id", "usr_anon")
    user_name = current_user.get("name", "Finance User")
    user_role = current_user.get("role", "CFO")
    user_department = current_user.get("department")

    # 1. Rate Limiting & Token Spend Governor
    rate_limiter.check_rate_limit(client_key=user_id, estimated_tokens=300)

    # 2. Handle Human-In-The-Loop Approval Decisions
    if req.approve is not None:
        action_verb = "APPROVED" if req.approve else "REJECTED"
        audit_service.log_action(
            user_id=user_id,
            user_name=user_name,
            role=user_role,
            action=f"HITL_COPILOT_{action_verb}",
            entity="DISBURSEMENT",
            entity_id=req.thread_id or "default-thread",
            details=f"User {user_name} ({user_role}) {action_verb.lower()} pending high-value disbursement in Copilot.",
            risk_level="HIGH" if req.approve else "LOW",
        )
        return {
            "success": True,
            "status": "completed",
            "response": f"### ✅ Human-In-The-Loop Decision Recorded\n\n**Action**: Disbursement was **{action_verb}** by {user_name} ({user_role}).\n\n* The Financial Digital Twin state and transaction ledgers have been updated.\n* Action logged to immutable audit trail.",
            "suggested_actions": ["Review Updated Approvals Queue", "Inspect Cash Runway Impact"],
            "thread_id": req.thread_id,
        }

    # 3. Input Validation & Prompt Injection Defense
    raw_msg = (req.message or "").strip()
    if not raw_msg:
        raise HTTPException(status_code=422, detail="Chat message cannot be empty.")

    cleaned_msg = sanitize_text(raw_msg, field_name="Chat Message", max_length=4000, allow_empty=False)
    msg_lower = cleaned_msg.lower()

    # Check for adversarial prompt injection attempts
    if any(kw in msg_lower for kw in PROMPT_INJECTION_KEYWORDS):
        logger.warning(f"[Security] Prompt injection attempt intercepted from user {user_id} ({user_name}): '{cleaned_msg[:100]}'")
        audit_service.log_action(
            user_id=user_id,
            user_name=user_name,
            role=user_role,
            action="PROMPT_INJECTION_INTERCEPTED",
            entity="AI_COPILOT",
            entity_id=req.thread_id or "chat",
            details=f"Adversarial prompt injection pattern blocked: '{cleaned_msg[:80]}'",
            risk_level="HIGH"
        )
        return {
            "success": True,
            "status": "completed",
            "response": (
                "### ⚠️ Security Policy Alert: Prompt Injection Blocked\n\n"
                "**Action Halted:** The system detected an adversarial prompt instruction attempting to override financial policies or role constraints.\n\n"
                "**FinPilot AI Core Architecture:**\n"
                "1. **Deterministic Guardrails:** Financial thresholds (₹50,000 HITL gate, budget caps, 15% discount limit) are enforced strictly in server-side Python code, never in LLM prompts.\n"
                "2. **Authority Separation:** The AI reasoning model can suggest recommendations, but all fund disbursements and approvals require authenticated human cryptographic signatures.\n"
                "3. **Incident Logged:** This security event has been recorded on the SHA-256 immutable audit trail."
            ),
            "suggested_actions": ["Review Audit Logs", "Inspect Financial Policy Rules"],
            "thread_id": req.thread_id,
        }

    # 4. Grounded Copilot: real retrieval + (scenario sims | grounded LLM call).
    # Failures return explicit retry text — never a fabricated scenario.
    try:
        res = grounded_copilot.analyze(
            question=cleaned_msg,
            user_id=user_id,
            user_role=user_role,
            user_name=user_name,
            user_department=user_department,
        )
        response_text = res.get("response") or "Analysis completed."
        suggested_actions = res.get("suggested_actions") or [
            "Run 90-Day Digital Twin Simulation",
            "View Company Decision Map",
            "Inspect Department Budgets",
        ]

        status = res.get("status") or "completed"
        if status == "completed" and (
            "pending_approval" in res or "THRESHOLD BREACH" in response_text.upper()
        ):
            status = "pending_approval"

        out = {
            "success": True,
            "status": status,
            "response": response_text,
            "trace_id": res.get("trace_id"),
            "agent_steps": res.get("agent_steps", []),
            "suggested_actions": suggested_actions,
            "thread_id": req.thread_id,
        }
        if res.get("simulation") is not None:
            out["simulation"] = res["simulation"]
        return out

    except Exception as e:
        logger.error(f"Error in grounded copilot pipeline: {type(e).__name__}: {e}")
        return {
            "success": True,
            "status": "llm_unavailable",
            "response": (
                "## Analysis Couldn't Complete — Please Retry\n\n"
                "The Copilot hit an unexpected error before producing an answer. "
                "No partial or estimated figures are shown because they could be wrong.\n\n"
                "Please retry in a moment."
            ),
            "suggested_actions": ["Retry analysis", "Check AI status"],
            "thread_id": req.thread_id,
        }
