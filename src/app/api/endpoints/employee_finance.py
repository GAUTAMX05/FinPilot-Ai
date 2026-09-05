import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.app.core.rbac import Permission
from src.app.core.auth_middleware import get_current_user, require_permission
from src.app.services.employee_finance_service import employee_finance_service

logger = logging.getLogger("EmployeeFinanceApi")
router = APIRouter()


class AddEmployeeRequest(BaseModel):
    employee_id: Optional[str] = None
    name: str
    email: str
    phone: Optional[str] = "+91 98000 00000"
    department: str
    designation: str
    salary_band: Optional[str] = "₹12–18 LPA"
    annual_ctc: Optional[float] = 1200000.0
    monthly_basic: float
    hra: Optional[float] = None
    special_allowance: Optional[float] = 5000.0
    bonus_variable: Optional[float] = 0.0
    pf_deduction: Optional[float] = None
    tds_deduction: Optional[float] = 5000.0
    joining_date: Optional[str] = None
    employment_type: Optional[str] = "Full-Time"
    manager: Optional[str] = "Vikramaditya S."
    location: Optional[str] = "Bangalore HQ"
    monthly_allowance_limit: Optional[float] = 15000.0
    annual_allowance_limit: Optional[float] = 180000.0


class ReviseSalaryRequest(BaseModel):
    new_basic: float
    effective_date: Optional[str] = None
    reason: str


class DeactivateEmployeeRequest(BaseModel):
    reason: Optional[str] = "Employee separated/relieved."


class EvaluateAllowanceRequest(BaseModel):
    category: str
    requested_limit: float


@router.get("")
def list_employees(current_user: dict = Depends(get_current_user)):
    """Lists employee financial profiles scoped by user role & department."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")
    employees = employee_finance_service.get_all_employees(user_role, user_dept)
    return {"success": True, "total_employees": len(employees), "employees": employees}


@router.post("")
def add_employee(
    payload: AddEmployeeRequest,
    current_user: dict = Depends(require_permission(Permission.CREATE_EXPENSE_REQUEST)),
):
    """Creates a new employee profile in the financial governance register."""
    try:
        res = employee_finance_service.add_employee(
            data=payload.model_dump(),
            user_id=current_user["id"],
            user_name=current_user["name"],
            user_role=current_user["role"],
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{employee_id}")
def get_employee_profile(employee_id: str, current_user: dict = Depends(get_current_user)):
    """Gets detailed financial profile, compensation breakdown, and job evaluation."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")
    try:
        emp = employee_finance_service.get_employee(employee_id, user_role, user_dept)
        if not emp:
            raise HTTPException(status_code=404, detail=f"Employee '{employee_id}' not found.")
        return {"success": True, "employee": emp}
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))


@router.put("/{employee_id}")
def update_employee(
    employee_id: str,
    payload: Dict[str, Any],
    current_user: dict = Depends(require_permission(Permission.CREATE_EXPENSE_REQUEST)),
):
    """Updates an employee record."""
    try:
        res = employee_finance_service.update_employee(
            employee_id=employee_id,
            data=payload,
            user_id=current_user["id"],
            user_name=current_user["name"],
            user_role=current_user["role"],
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{employee_id}/deactivate")
def deactivate_employee(
    employee_id: str,
    payload: DeactivateEmployeeRequest,
    current_user: dict = Depends(require_permission(Permission.MODIFY_BUDGET)),
):
    """Deactivates an employee rather than wiping financial audit records."""
    try:
        res = employee_finance_service.deactivate_employee(
            employee_id=employee_id,
            reason=payload.reason or "",
            user_id=current_user["id"],
            user_name=current_user["name"],
            user_role=current_user["role"],
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{employee_id}")
def delete_employee(
    employee_id: str,
    current_user: dict = Depends(require_permission(Permission.FINAL_APPROVAL)),
):
    """Safely deletes an employee if no historical financial claims exist."""
    try:
        res = employee_finance_service.delete_employee(
            employee_id=employee_id,
            user_id=current_user["id"],
            user_name=current_user["name"],
            user_role=current_user["role"],
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{employee_id}/revise-salary")
def revise_salary(
    employee_id: str,
    payload: ReviseSalaryRequest,
    current_user: dict = Depends(require_permission(Permission.FINAL_APPROVAL)),
):
    """Authorizes an executive salary revision and logs to audit trail."""
    try:
        res = employee_finance_service.revise_salary(
            employee_id=employee_id,
            new_basic=payload.new_basic,
            effective_date=payload.effective_date or "",
            reason=payload.reason,
            user_id=current_user["id"],
            user_name=current_user["name"],
            user_role=current_user["role"],
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{employee_id}/evaluate-allowance-request")
def evaluate_allowance_request(
    employee_id: str,
    payload: EvaluateAllowanceRequest,
    current_user: dict = Depends(get_current_user),
):
    """Runs deterministic rule assessment on allowance requests."""
    try:
        res = employee_finance_service.evaluate_allowance_request(
            employee_id=employee_id,
            category=payload.category,
            requested_limit=payload.requested_limit,
        )
        return {"success": True, "assessment": res}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


class EvaluateAllowanceQuickRequest(BaseModel):
    category: str
    requested_limit: Optional[float] = None


@router.post("/{employee_id}/evaluate-allowance")
def evaluate_allowance_quick(
    employee_id: str,
    payload: EvaluateAllowanceQuickRequest,
    current_user: dict = Depends(get_current_user),
):
    """UI alias for allowance evaluation: when no requested limit is given,
    evaluates against the employee's current category limit."""
    try:
        requested = payload.requested_limit
        if requested is None:
            emp = employee_finance_service.get_employee(
                employee_id,
                current_user.get("role"),
                current_user.get("department"),
            )
            if not emp:
                raise HTTPException(status_code=404, detail=f"Employee '{employee_id}' not found.")
            requested = float(
                emp.get("allowance_policy", {}).get(payload.category.lower(), {}).get("monthly_limit", 10000.0)
            )
        res = employee_finance_service.evaluate_allowance_request(
            employee_id=employee_id,
            category=payload.category,
            requested_limit=requested,
        )
        return {"success": True, "assessment": res}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/anomalies/allowance")
def get_allowance_anomalies(current_user: dict = Depends(get_current_user)):
    """Detects allowance limit breaches, duplicate claims, and policy anomalies."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")
    anomalies = employee_finance_service.detect_allowance_anomalies(user_role, user_dept)
    return {"success": True, "total_anomalies": len(anomalies), "anomalies": anomalies}
