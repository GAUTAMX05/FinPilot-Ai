from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from src.app.core.rbac import Permission
from src.app.core.auth_middleware import get_current_user, require_permission
from src.app.services.audit_service import audit_service

router = APIRouter(prefix="/audit", tags=["Compliance & Audit Logs"])


class FlagTransactionRequest(BaseModel):
    invoice_id: str
    reason: str
    risk_level: str = "HIGH"


@router.get("/logs")
def get_audit_logs(
    limit: int = 50,
    current_user: dict = Depends(require_permission(Permission.VIEW_AUDIT_LOGS)),
):
    """Returns immutable financial audit logs (CFO and Auditor only)."""
    return {
        "success": True,
        "total_logs": len(audit_service.get_audit_logs(limit)),
        "logs": audit_service.get_audit_logs(limit),
    }


@router.get("/metrics")
def get_audit_metrics(
    current_user: dict = Depends(require_permission(Permission.VIEW_FINANCIAL_REPORTS)),
):
    """Returns audit and risk telemetry indicators."""
    return {
        "success": True,
        "metrics": audit_service.get_audit_metrics(),
        "flags": audit_service.get_audit_flags(),
    }


@router.post("/flag")
def flag_transaction(
    req: FlagTransactionRequest,
    current_user: dict = Depends(require_permission(Permission.FLAG_TRANSACTION)),
):
    """Allows Auditor, Finance Manager, or CFO to flag an invoice for compliance review."""
    flag = audit_service.flag_transaction(
        user_id=current_user["id"],
        user_name=current_user["name"],
        role=current_user["role"],
        entity_id=req.invoice_id,
        reason=req.reason,
        risk_level=req.risk_level,
    )
    return {
        "success": True,
        "message": f"Invoice {req.invoice_id} successfully flagged for compliance review.",
        "flag": flag,
    }
