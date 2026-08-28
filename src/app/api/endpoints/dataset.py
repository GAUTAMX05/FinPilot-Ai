from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from src.app.core.auth_middleware import get_current_user
from src.app.services.dataset_service import dataset_service

router = APIRouter(prefix="/dataset", tags=["Enterprise Dataset & Date-Span Analytics"])


@router.get("/summary")
def get_dataset_summary(
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    current_user: dict = Depends(get_current_user),
):
    """Returns aggregated KPIs and department spend for the chosen date span."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")
    res = dataset_service.get_summary(start_date, end_date, user_role, user_dept)
    return {"success": True, "data": res}


@router.get("/invoices")
def get_filtered_invoices(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Returns 220 invoices filtered by date span and status."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")
    invoices = dataset_service.get_invoices(start_date, end_date, user_role, user_dept, status)
    return {"success": True, "count": len(invoices), "invoices": invoices}


@router.get("/transactions")
def get_filtered_transactions(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    direction: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Returns 500 Razorpay and bank transactions filtered by date span."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")
    txns = dataset_service.get_transactions(start_date, end_date, user_role, user_dept, direction, status)
    return {"success": True, "count": len(txns), "transactions": txns}


@router.get("/employees")
def get_all_employees(current_user: dict = Depends(get_current_user)):
    """Returns all 100 employee profiles across 5 departments."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")
    emps = dataset_service.get_employees(user_role, user_dept)
    return {"success": True, "count": len(emps), "employees": emps}


@router.get("/allowances")
def get_all_allowances(current_user: dict = Depends(get_current_user)):
    """Returns 200 employee allowances (Travel & Food) with policy limit status."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")
    allow = dataset_service.get_allowances(user_role, user_dept)
    return {"success": True, "count": len(allow), "allowances": allow}


@router.get("/payroll")
def get_payroll_records(
    period: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Returns 100 employee payroll records with basic, gross, TDS, and net breakdown."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")
    pay = dataset_service.get_payroll(user_role, user_dept, period)
    return {"success": True, "count": len(pay), "payroll": pay}


@router.get("/form16")
def get_form16_records(current_user: dict = Depends(get_current_user)):
    """Returns 100 Form 16 reconciliation records."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")
    f16 = dataset_service.get_form16(user_role, user_dept)
    return {"success": True, "count": len(f16), "form16": f16}


@router.get("/spending-trends")
def get_spending_trends(current_user: dict = Depends(get_current_user)):
    """Returns multi-month spending across April to August 2026."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")
    sp = dataset_service.get_spending_trends(user_role, user_dept)
    return {"success": True, "spending": sp}
