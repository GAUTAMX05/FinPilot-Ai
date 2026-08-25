import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from src.app.core.rbac import Permission, Role
from src.app.core.auth_middleware import get_current_user, require_permission
from src.app.services.intelligence_service import intelligence_service

logger = logging.getLogger("IntelligenceApi")
router = APIRouter()


class AffordabilityRequest(BaseModel):
    amount: float
    department: str
    category: str = "General"
    description: str = ""


class DuplicateCheckRequest(BaseModel):
    vendor_name: str
    amount: float
    department: str
    description: str = ""
    invoice_id: Optional[str] = None


@router.get("/health-score")
def get_health_score(current_user: dict = Depends(get_current_user)):
    """Computes the real-time Financial Health Score (0-100) and explainability factors."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")
    res = intelligence_service.calculate_health_score(user_role, user_dept)
    return {"success": True, "data": res}


@router.get("/forecasts")
def get_forecasts(current_user: dict = Depends(get_current_user)):
    """Predicts year-end spending, monthly burn rate, and deficit risk for authorized departments."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")
    forecasts = intelligence_service.get_department_forecasts(user_role, user_dept)
    return {"success": True, "forecasts": forecasts}


@router.get("/analytics-series")
def get_analytics_series(
    metric: str = Query("spending", description="Metric to visualize: spending, budget_utilization, cash_flow, committed_spend, payroll"),
    period: str = Query("daily", description="Time aggregation: daily, weekly, monthly"),
    current_user: dict = Depends(get_current_user),
):
    """Returns dynamic time-series aggregation across Daily, Weekly, and Monthly horizons."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")
    res = intelligence_service.get_analytics_series(
        metric=metric,
        period=period,
        user_role=user_role,
        user_department=user_dept,
    )
    return res


@router.get("/decision-tree-eval")
def get_decision_tree_eval(
    event_id: str = Query("EXP-2026-8801", description="Financial event / claim ID"),
    current_user: dict = Depends(get_current_user),
):
    """Simulates interactive decision tree pipeline nodes for financial events."""
    res = intelligence_service.evaluate_decision_tree(event_id)
    return {"success": True, "decision_tree": res}


@router.get("/company-decision-map")
def get_company_decision_map(current_user: dict = Depends(get_current_user)):
    """Hierarchical decision map of company budgets, liquidity runways, and compliance."""
    res = intelligence_service.get_company_decision_map()
    return {"success": True, "decision_map": res}


@router.post("/affordability")
def simulate_affordability(
    req: AffordabilityRequest,
    current_user: dict = Depends(get_current_user),
):
    """'Can We Afford This?' scenario simulation."""
    try:
        res = intelligence_service.simulate_affordability(
            amount=req.amount,
            department=req.department,
            category=req.category,
        )
        return {"success": True, "simulation": res}
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/watchtower")
def get_watchtower_alerts(current_user: dict = Depends(get_current_user)):
    """Returns active financial alerts, deficit warnings, and anomaly telemetry."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")
    alerts = intelligence_service.get_watchtower_alerts(user_role, user_dept)
    return {"success": True, "total_alerts": len(alerts), "alerts": alerts}


@router.get("/proposals")
def get_proposals(current_user: dict = Depends(get_current_user)):
    """Returns strategic budget and spend optimization proposals."""
    proposals = intelligence_service.get_proposals()
    return {"success": True, "total_proposals": len(proposals), "proposals": proposals}


@router.get("/vendors")
def get_vendor_intelligence(current_user: dict = Depends(get_current_user)):
    """Vendor concentration, average ticket sizes, and anomaly frequency radar."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")
    vendors = intelligence_service.get_vendor_intelligence(user_role, user_dept)
    return {"success": True, "total_vendors": len(vendors), "vendors": vendors}


@router.get("/report")
def get_executive_report(current_user: dict = Depends(get_current_user)):
    """Synthesizes an executive brief of corporate financial posture."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")
    report = intelligence_service.generate_executive_report(user_role, user_dept)
    return {"success": True, "report": report}
