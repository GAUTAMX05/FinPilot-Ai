# -*- coding: utf-8 -*-
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from src.app.core.rbac import Permission
from src.app.core.auth_middleware import get_current_user, require_permission
from src.app.core.validators import validate_monetary_amount, validate_department, sanitize_text
from src.app.services.invoice_service import invoice_service
from src.app.services.anomaly_service import anomaly_service
from src.app.services.audit_service import audit_service

router = APIRouter(prefix="/invoices", tags=["Invoices & Expenses"])


class InvoiceCreateRequest(BaseModel):
    vendor_name: str = Field(..., max_length=100)
    department: str = Field(..., max_length=50)
    category: Optional[str] = Field(default="General", max_length=50)
    subtotal: Optional[float] = None
    tax_gst: Optional[float] = None
    total_amount: Optional[float] = None
    amount: Optional[float] = None
    po_number: Optional[str] = Field(default="", max_length=50)
    description: Optional[str] = Field(default="", max_length=500)
    items: Optional[List[Dict[str, Any]]] = []


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

    valid_dept = validate_department(req.department)
    if user_role == "DEPARTMENT_HEAD" and user_dept:
        if valid_dept.lower() != user_dept.strip().lower():
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: You can only audit invoices for your department ({user_dept}).",
            )

    raw_amt = req.total_amount if req.total_amount is not None else req.amount
    valid_amount = validate_monetary_amount(raw_amt, field_name="Invoice Total Amount", min_amount=1.0)

    audit_payload = req.model_dump()
    audit_payload["department"] = valid_dept
    audit_payload["total_amount"] = valid_amount
    res = anomaly_service.audit_invoice(audit_payload)
    return {"success": True, "audit": res}


@router.post("")
def create_invoice_endpoint(
    req: InvoiceCreateRequest,
    current_user: dict = Depends(require_permission(Permission.CREATE_EXPENSE_REQUEST)),
):
    """Submits a new invoice / expense claim with strict validation."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")

    valid_dept = validate_department(req.department)
    if user_role == "DEPARTMENT_HEAD" and user_dept:
        if valid_dept.lower() != user_dept.strip().lower():
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: Department Heads can only submit invoices for their assigned department ({user_dept}).",
            )

    clean_vendor = sanitize_text(req.vendor_name, field_name="Vendor Name", max_length=100, allow_empty=False)
    clean_cat = sanitize_text(req.category or "General", field_name="Category", max_length=50)
    raw_amt = req.total_amount if req.total_amount is not None else req.amount
    valid_amount = validate_monetary_amount(raw_amt, field_name="Invoice Total Amount", min_amount=1.0)

    invoice_data = {
        "vendor_name": clean_vendor,
        "department": valid_dept,
        "category": clean_cat,
        "amount": valid_amount,
        "total_amount": valid_amount,
        "subtotal": req.subtotal or round(valid_amount / 1.18, 2),
        "tax_gst": req.tax_gst or round(valid_amount * 0.18 / 1.18, 2),
        "po_number": sanitize_text(req.po_number, field_name="PO Number", max_length=50),
        "description": sanitize_text(req.description, field_name="Description", max_length=500),
        "status": "Pending Review",
        "created_by": current_user.get("name", "User"),
    }

    new_inv = invoice_service.add_invoice(invoice_data)

    # Immutable audit trail
    audit_service.log_action(
        user_id=current_user["id"],
        user_name=current_user["name"],
        role=current_user["role"],
        action="INVOICE_SUBMITTED",
        entity="INVOICE",
        entity_id=new_inv.get("invoice_id", "INV-UNKNOWN"),
        details=f"Submitted invoice for ₹{valid_amount:,.2f} from vendor '{clean_vendor}' in {valid_dept}.",
        risk_level="LOW" if valid_amount < 50000.0 else "MEDIUM",
    )

    return {"success": True, "invoice": new_inv}
