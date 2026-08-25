import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.app.core.rbac import Permission
from src.app.core.auth_middleware import get_current_user, require_permission
from src.app.services.payroll_service import payroll_service

logger = logging.getLogger("PayrollApi")
router = APIRouter()


class ResolveTaxRequest(BaseModel):
    resolution_note: Optional[str] = "Verified against adjusted salary annexure."


@router.get("/summary")
def get_payroll_summary(current_user: dict = Depends(get_current_user)):
    """Monthly payroll register summary and salary gross cross-check telemetry."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")
    res = payroll_service.get_payroll_summary(user_role, user_dept)
    return {"success": True, "payroll": res}


@router.get("/tax-reconciliation")
def get_tax_reconciliation(current_user: dict = Depends(get_current_user)):
    """Form 16 vs 26AS TDS & salary reporting reconciliation telemetry."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")
    res = payroll_service.get_tax_reconciliation(user_role, user_dept)
    return {"success": True, "tax_reconciliation": res}


@router.post("/tax-reconciliation/{employee_id}/resolve")
def resolve_tax_record(
    employee_id: str,
    payload: ResolveTaxRequest,
    current_user: dict = Depends(require_permission(Permission.AUDIT_INVOICE)),
):
    """Marks a tax reporting mismatch as reviewed and resolved."""
    try:
        res = payroll_service.resolve_tax_record(
            employee_id=employee_id,
            resolution_note=payload.resolution_note or "",
            user_id=current_user["id"],
            user_name=current_user["name"],
            user_role=current_user["role"],
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/tax-reconciliation/{employee_id}/notify-finance")
def notify_finance_tax(
    employee_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Alerts Finance Operations regarding Form 16 / TDS difference."""
    try:
        res = payroll_service.notify_finance_for_tax(
            employee_id=employee_id,
            user_name=current_user["name"],
            user_role=current_user["role"],
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/headcount-forecast")
def get_headcount_forecast(
    current_user: dict = Depends(require_permission(Permission.FINAL_APPROVAL)),
):
    """Total Employee Cost breakdown and 6/12/24-month headcount growth forecast (CFO only)."""
    res = payroll_service.get_headcount_cost_analytics()
    return {"success": True, "headcount_analytics": res}
