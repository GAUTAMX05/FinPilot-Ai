from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from src.app.core.rbac import Permission, Role
from src.app.core.auth_middleware import get_current_user, require_permission
from src.app.core.config import settings
from src.app.services.invoice_service import invoice_service
from src.app.services.budget_service import budget_service
from src.app.services.audit_service import audit_service

router = APIRouter(prefix="/approvals", tags=["HITL Financial Approvals"])


class ApprovalDecisionRequest(BaseModel):
    invoice_id: str
    approved: bool
    reviewer_comments: str = ""


@router.get("/pending")
def get_pending_approvals(current_user: dict = Depends(get_current_user)):
    """Lists all invoices currently waiting for approval scoped by user role & department."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")
    pending = invoice_service.get_pending_invoices(user_role, user_dept)
    return {"success": True, "total_pending": len(pending), "pending_invoices": pending}


@router.post("/decide")
def decide_approval(
    req: ApprovalDecisionRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Submits manager approval or rejection decision with strict RBAC & segregation of duties.
    """
    user_role = current_user.get("role")
    user_dept = current_user.get("department")
    user_id = current_user.get("id")

    # 1. Auditor check
    if user_role == Role.AUDITOR.value:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Auditors cannot approve or reject financial disbursements. Use /audit/flag to flag transactions.",
        )

    inv = invoice_service.get_invoice_by_id(req.invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Invoice '{req.invoice_id}' not found.")

    amt = float(inv.get("total_amount", 0.0))
    dept = inv.get("department", "Operations")
    submitted_by = inv.get("submitted_by_id")

    # 2. Segregation of duties: Department Head cannot approve their own submission
    if user_role == Role.DEPARTMENT_HEAD.value:
        if user_dept and dept.lower() != user_dept.lower():
            raise HTTPException(status_code=403, detail=f"Forbidden: You can only decide approvals for {user_dept}.")
        if submitted_by and submitted_by == user_id:
            raise HTTPException(
                status_code=403,
                detail="Segregation of Duties Violation: You cannot approve your own submitted expense request.",
            )

    # 3. High-Value Authorization Threshold: Finance Manager cannot approve >= ₹50,000
    if user_role == Role.FINANCE_MANAGER.value and req.approved:
        if amt >= settings.HITL_APPROVAL_THRESHOLD_INR:
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: Amounts >= ₹{settings.HITL_APPROVAL_THRESHOLD_INR:,.2f} require CFO Final Authorization.",
            )

    new_status = "approved" if req.approved else "rejected"
    invoice_service.update_invoice_status(
        invoice_id=req.invoice_id,
        new_status=new_status,
        decided_by_id=current_user["id"],
        decided_by_name=current_user["name"],
        comments=req.reviewer_comments,
    )

    if req.approved:
        budget_service.commit_expense(dept, amt, was_pending=True)
    else:
        budget_service.release_reservation(dept, amt)

    audit_service.log_action(
        user_id=current_user["id"],
        user_name=current_user["name"],
        role=current_user["role"],
        action="APPROVE_EXPENSE" if req.approved else "REJECT_EXPENSE",
        entity="INVOICE",
        entity_id=req.invoice_id,
        old_value="PENDING_APPROVAL",
        new_value=new_status.upper(),
        details=f"{'Approved' if req.approved else 'Rejected'} ₹{amt:,.2f} for {dept}. Comments: {req.reviewer_comments}",
        risk_level="HIGH" if amt >= settings.HITL_APPROVAL_THRESHOLD_INR else "LOW",
    )

    return {
        "success": True,
        "invoice_id": req.invoice_id,
        "status": new_status,
        "decided_by": current_user["name"],
        "comments": req.reviewer_comments,
    }
