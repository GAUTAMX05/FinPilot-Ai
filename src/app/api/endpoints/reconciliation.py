import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.app.core.rbac import Permission
from src.app.core.auth_middleware import get_current_user, require_permission
from src.app.services.reconciliation_service import reconciliation_service

logger = logging.getLogger("ReconciliationApi")
router = APIRouter(prefix="/reconciliation", tags=["Reconciliation & Exception Center"])


class ResolveExceptionRequest(BaseModel):
    decision: str  # "MATCHED", "REJECTED", "INVESTIGATING"
    comments: str = ""


@router.post("/run")
def run_reconciliation(
    current_user: dict = Depends(require_permission(Permission.VIEW_FINANCIAL_REPORTS)),
):
    """Executes Two-Stage Hybrid Reconciliation across Bank, Ledger, and Gateway records."""
    res = reconciliation_service.run_reconciliation()
    return res


@router.get("/exceptions")
def get_exceptions(current_user: dict = Depends(get_current_user)):
    """Returns open financial reconciliation exceptions."""
    exceptions = reconciliation_service.get_exceptions()
    return {"success": True, "total_exceptions": len(exceptions), "exceptions": exceptions}


@router.post("/exceptions/{exception_id}/resolve")
def resolve_exception(
    exception_id: str,
    req: ResolveExceptionRequest,
    current_user: dict = Depends(require_permission(Permission.AUDIT_INVOICE)),
):
    """Resolves an ambiguous transaction exception with human sign-off."""
    try:
        res = reconciliation_service.resolve_exception(
            exception_id=exception_id,
            decision=req.decision,
            user_id=current_user["id"],
            user_name=current_user["name"],
            user_role=current_user["role"],
            comments=req.comments,
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
