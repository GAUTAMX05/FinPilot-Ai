from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from src.app.core.rbac import Permission
from src.app.core.auth_middleware import get_current_user, require_permission
from src.app.services.invoice_service import invoice_service
from src.app.services.anomaly_service import anomaly_service
from src.app.services.audit_service import audit_service

router = APIRouter(prefix="/invoices", tags=["Invoices & Expenses"])


class InvoiceCreateRequest(BaseModel):
    vendor_name: str
    department: str
    category: str
    subtotal: float
    tax_gst: float
    total_amount: float
    po_number: str = ""
    description: str = ""
    items: List[Dict[str, Any]] = []


@router.get("")
def list_invoices(current_user: dict = Depends(get_current_user)):
    """Lists invoices visible to current user's role and department."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")
    invoices = invoice_service.get_all_invoices(user_role, user_dept)
    return {"success": True, "invoices": invoices}


@router.post("/audit")
def audit_invoice_endpoint(
    req: InvoiceCreateRequest,
    current_user: dict = Depends(require_permission(Permission.AUDIT_INVOICE)),
):
    """Audits an invoice for tax math, duplicate charges, and policy compliance."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")

    if user_role == "DEPARTMENT_HEAD" and user_dept:
        if req.department.strip().lower() != user_dept.strip().lower():
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: You can only audit invoices for your department ({user_dept}).",
            )

    res = anomaly_service.audit_invoice(req.model_dump())
    return {"success": True, "audit": res}


@router.post("")
def create_invoice_endpoint(
    req: InvoiceCreateRequest,
    current_user: dict = Depends(require_permission(Permission.CREATE_EXPENSE_REQUEST)),
):
    """Submits a new invoice / expense claim."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")

    if user_role == "DEPARTMENT_HEAD" and user_dept:
        if req.department.strip().lower() != user_dept.strip().lower():
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: You can only submit expenses for your department ({user_dept}).",
            )

    audit_res = anomaly_service.audit_invoice(req.model_dump())
    status = "pending_approval" if audit_res.get("requires_hitl") else "approved"
    
    data = req.model_dump()
    data["status"] = status
    data["requires_hitl"] = audit_res.get("requires_hitl")
    data["audit_flags"] = audit_res.get("flags", [])
    data["submitted_by_id"] = current_user["id"]
    data["submitted_by_name"] = current_user["name"]
    data["submitted_by_role"] = current_user["role"]

    created = invoice_service.add_invoice(data)

    audit_service.log_action(
        user_id=current_user["id"],
        user_name=current_user["name"],
        role=current_user["role"],
        action="SUBMIT_EXPENSE",
        entity="INVOICE",
        entity_id=created["invoice_id"],
        new_value=f"₹{created['total_amount']:,.2f} INR ({created['department']})",
        details=f"Submitted expense to {created['vendor_name']} by {current_user['name']}",
        risk_level="MEDIUM" if audit_res.get("requires_hitl") else "LOW",
    )

    return {"success": True, "invoice": created, "audit": audit_res}
