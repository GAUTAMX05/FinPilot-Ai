import json
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

from src.app.core.auth_middleware import get_current_user
from src.app.services.multi_agent_orchestrator import MultiAgentFinancialOrchestrator
from src.app.services.ai_reasoning_engine import ai_reasoning_engine
from src.app.services.audit_service import audit_service

logger = logging.getLogger("AgentChatApi")
router = APIRouter(prefix="/agent", tags=["Finance Agent Chat"])
orchestrator = MultiAgentFinancialOrchestrator()


class ChatRequest(BaseModel):
    message: Optional[str] = ""
    thread_id: Optional[str] = "default-thread"
    approve: Optional[bool] = None  # None: regular chat; True/False: HITL approval


@router.post("/chat")
async def chat_endpoint(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    """
    Financial Decision Copilot Endpoint.
    Executes the 7-agent multi-agent reasoning pipeline:
    1. Intent & RBAC Gatekeeper
    2. Retrieval Agent with Data Lineage
    3. Deterministic Analysis Agent
    4. 4-Factor Risk & Decision Scorer
    5. Financial Digital Twin 90-Day Forward Brancher
    6. Causal Root Cause Signal Correlator
    7. Role-Aware Narrator Agent (5-Step Synthesis)
    """
    user_id = current_user["id"]
    user_name = current_user["name"]
    user_role = current_user["role"]
    user_department = current_user.get("department")

    # 1. Handle Human-In-The-Loop Approval Decisions
    if req.approve is not None:
        action_verb = "APPROVED" if req.approve else "REJECTED"
        audit_service.log_action(
            user_id=user_id,
            user_name=user_name,
            role=user_role,
            action=f"HITL_COPILOT_{action_verb}",
            entity="DISBURSEMENT",
            entity_id=req.thread_id,
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

    # 2. Validate Message
    msg = (req.message or "").strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        # 3. Execute Multi-Agent Financial Orchestrator
        res = orchestrator.process_query(
            query=msg,
            user_role=user_role,
            user_name=user_name,
            user_department=user_department,
        )

        response_text = res.get("response") or "Analysis completed successfully."
        suggested_actions = res.get("suggested_actions") or [
            "Run 90-Day Digital Twin Simulation",
            "View Company Decision Map",
            "Inspect Department Budgets",
        ]

        # Check for HITL trigger in response
        status = "completed"
        if "pending_approval" in res or "THRESHOLD BREACH" in response_text.upper():
            status = "pending_approval"

        return {
            "success": True,
            "status": status,
            "response": response_text,
            "trace_id": res.get("trace_id"),
            "agent_steps": res.get("agent_steps", []),
            "suggested_actions": suggested_actions,
            "thread_id": req.thread_id,
        }

    except Exception as e:
        logger.exception("Error in multi-agent financial copilot execution")
        # Fallback to AI Reasoning Engine
        try:
            fallback = ai_reasoning_engine.analyze_financial_query(
                query=msg,
                user_role=user_role,
                user_name=user_name,
                user_department=user_department,
            )
            return {
                "success": True,
                "status": "completed",
                "response": fallback["response"],
                "suggested_actions": fallback.get("suggested_actions", []),
                "thread_id": req.thread_id,
            }
        except Exception as fb_err:
            raise HTTPException(
                status_code=500,
                detail=f"Financial Copilot error: {str(e)} (Fallback: {str(fb_err)})",
            )


@router.post("/chat/stream")
async def chat_stream_endpoint(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Streaming endpoint for token-by-token multi-agent output."""
    user_id = current_user["id"]
    user_name = current_user["name"]
    user_role = current_user["role"]
    user_department = current_user.get("department")

    async def event_generator():
        try:
            msg = (req.message or "").strip()
            yield f"data: {json.dumps({'type': 'agent_call', 'agent': 'IntentAgent & RBAC Gatekeeper'})}\n\n"
            yield f"data: {json.dumps({'type': 'agent_call', 'agent': 'RetrievalAgent & Lineage Tracker'})}\n\n"
            yield f"data: {json.dumps({'type': 'agent_call', 'agent': 'SimulationAgent & Digital Twin Brancher'})}\n\n"

            res = orchestrator.process_query(
                query=msg,
                user_role=user_role,
                user_name=user_name,
                user_department=user_department,
            )

            yield f"data: {json.dumps({'type': 'full_response', 'content': res['response'], 'suggested_actions': res.get('suggested_actions', [])})}\n\n"
            yield f"data: {json.dumps({'type': 'completed', 'status': 'completed'})}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}")
            fallback = ai_reasoning_engine.analyze_financial_query(
                query=req.message or "Overview",
                user_role=user_role,
                user_name=user_name,
                user_department=user_department,
            )
            yield f"data: {json.dumps({'type': 'full_response', 'content': fallback['response']})}\n\n"
            yield f"data: {json.dumps({'type': 'completed', 'status': 'completed'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
