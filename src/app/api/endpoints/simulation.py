from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from src.app.core.rbac import Role
from src.app.core.auth_middleware import get_current_user
from src.app.services.digital_twin_service import digital_twin_service
from src.app.services.multi_agent_orchestrator import multi_agent_orchestrator
from src.app.services.policy_calibration_service import policy_calibration_service

router = APIRouter(prefix="/simulation", tags=["Financial Digital Twin & Simulation Engine"])


class WhatIfRequest(BaseModel):
    scenario: str = Field(description="Natural language what-if query or parameter description.")
    parameters: Optional[Dict[str, Any]] = None


class ApplyCalibrationRequest(BaseModel):
    proposal_id: str


@router.get("/digital-twin-state")
def get_digital_twin_state(current_user: dict = Depends(get_current_user)):
    """
    Returns the live synchronized Financial Digital Twin state snapshot
    along with 90-day baseline trajectory projections.
    """
    state = digital_twin_service.get_live_state(force_refresh=True)
    baseline_sim = digital_twin_service.simulate_forward(days=90, modifiers={})
    return {
        "success": True,
        "state": state,
        "baseline_90d_trajectory": {
            "labels": baseline_sim["labels"],
            "cash_trajectory": baseline_sim["cash_trajectory"],
            "burn_trajectory": baseline_sim["monthly_burn_trajectory"],
            "final_liquidity": baseline_sim["final_liquidity"],
            "projected_runway_days": baseline_sim["projected_runway_days"],
        }
    }


@router.post("/what-if")
def run_what_if_simulation(req: WhatIfRequest, current_user: dict = Depends(get_current_user)):
    """
    Executes a counterfactual what-if simulation against the Financial Digital Twin.
    Generates quantitative Before vs. After state deltas and role-aware explanations.
    """
    user_role = current_user.get("role", "CFO")
    user_name = current_user.get("name", "User")
    user_dept = current_user.get("department")

    orch_res = multi_agent_orchestrator.process_query(
        query=req.scenario,
        user_role=user_role,
        user_name=user_name,
        user_department=user_dept,
    )

    return {
        "success": True,
        "trace_id": orch_res.get("trace_id"),
        "intent": orch_res.get("intent"),
        "simulation": orch_res.get("simulation"),
        "causal_analysis": orch_res.get("causal_analysis"),
        "narrative": orch_res.get("response", {}).get("formatted_text"),
        "agent_steps": orch_res.get("agent_steps"),
        "suggested_actions": orch_res.get("suggested_actions"),
    }


@router.get("/causal-analysis")
def get_causal_analysis(
    anomaly_query: Optional[str] = "Engineering budget overrun",
    current_user: dict = Depends(get_current_user)
):
    """
    Correlates financial anomalies against operational signals to pinpoint root causes.
    """
    user_dept = current_user.get("department")
    causal_data = multi_agent_orchestrator._run_causal_correlation(
        query=anomaly_query or "Engineering budget overrun",
        user_department=user_dept,
    )
    return {"success": True, "causal_analysis": causal_data}


@router.get("/policy-calibrations")
def get_policy_calibrations(current_user: dict = Depends(get_current_user)):
    """
    Returns active self-calibrating policy suggestions derived from human override patterns.
    """
    proposals = policy_calibration_service.get_calibration_proposals()
    return {"success": True, "total_proposals": len(proposals), "proposals": proposals}


@router.post("/apply-policy-calibration")
def apply_policy_calibration(req: ApplyCalibrationRequest, current_user: dict = Depends(get_current_user)):
    """
    Applies an approved policy calibration (Restricted to CFO / Finance Manager).
    """
    user_role = current_user.get("role")
    if user_role not in [Role.CFO.value, Role.FINANCE_MANAGER.value]:
        raise HTTPException(status_code=403, detail="Forbidden: Only CFO or Finance Manager can apply policy calibrations.")

    try:
        res = policy_calibration_service.apply_calibration(
            proposal_id=req.proposal_id,
            actor_id=current_user.get("id", "usr_cfo"),
            actor_name=current_user.get("name", "CFO"),
            actor_role=user_role,
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
