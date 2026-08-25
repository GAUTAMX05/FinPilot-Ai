from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from src.app.core.rbac import Permission
from src.app.core.auth_middleware import get_current_user, require_permission
from src.app.services.budget_service import budget_service

router = APIRouter(prefix="/budgets", tags=["Department Budgets"])


class ModifyBudgetRequest(BaseModel):
    department: str
    new_allocated_budget: float
    reason: str = "Budget adjustment"


class ReallocateBudgetRequest(BaseModel):
    from_department: str
    to_department: str
    amount: float
    reason: str = "Inter-department budget reallocation"


@router.get("")
def get_all_budgets(current_user: dict = Depends(get_current_user)):
    """
    Returns department budgets.
    If caller is Department Head, returns only their assigned department.
    """
    user_role = current_user.get("role")
    user_dept = current_user.get("department")

    return {
        "success": True,
        "departments": budget_service.get_all_departments(user_role, user_dept),
        "user_role": user_role,
        "user_department": user_dept,
    }


@router.get("/{department}")
def get_department_budget(department: str, current_user: dict = Depends(get_current_user)):
    """Returns budget utilization for a specific department."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")

    res = budget_service.get_department_budget(department, user_role, user_dept)
    if not res:
        raise HTTPException(
            status_code=403 if user_role == "DEPARTMENT_HEAD" and user_dept and department.lower() != user_dept.lower() else 404,
            detail=f"Access denied or department '{department}' not found.",
        )
    return {"success": True, "data": res}


@router.post("/modify")
def modify_budget(
    req: ModifyBudgetRequest,
    current_user: dict = Depends(require_permission(Permission.MODIFY_BUDGET)),
):
    """Modifies a department budget allocation (CFO / Finance Manager)."""
    try:
        res = budget_service.modify_department_budget(
            department=req.department,
            new_allocated_budget=req.new_allocated_budget,
            user_id=current_user["id"],
            user_name=current_user["name"],
            role=current_user["role"],
            reason=req.reason,
        )
        return {"success": True, "data": res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reallocate")
def reallocate_budget(
    req: ReallocateBudgetRequest,
    current_user: dict = Depends(require_permission(Permission.FINAL_APPROVAL)),
):
    """Reallocates budget from one department to another (CFO exclusive)."""
    try:
        res = budget_service.reallocate_budget(
            from_department=req.from_department,
            to_department=req.to_department,
            amount=req.amount,
            user_id=current_user["id"],
            user_name=current_user["name"],
            role=current_user["role"],
            reason=req.reason,
        )
        return {"success": True, "data": res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
