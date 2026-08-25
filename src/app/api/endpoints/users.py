from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from src.app.core.rbac import Permission, Role
from src.app.core.auth_middleware import require_permission
from src.app.services.auth_service import auth_service
from src.app.services.audit_service import audit_service

router = APIRouter(prefix="/users", tags=["User Management (CFO Only)"])


class CreateUserRequest(BaseModel):
    name: str
    email: str
    password: str = "password123"
    role: Role
    department: Optional[str] = None


@router.get("")
def list_users(
    current_user: dict = Depends(require_permission(Permission.MANAGE_USERS)),
):
    """Lists all user accounts in the system (CFO exclusive)."""
    return {
        "success": True,
        "users": auth_service.list_all_users(),
    }


@router.post("")
def create_user_endpoint(
    req: CreateUserRequest,
    current_user: dict = Depends(require_permission(Permission.MANAGE_USERS)),
):
    """Creates a new user account (CFO exclusive)."""
    try:
        created = auth_service.create_user(req.model_dump())
        audit_service.log_action(
            user_id=current_user["id"],
            user_name=current_user["name"],
            role=current_user["role"],
            action="CREATE_USER",
            entity="USER_ACCOUNT",
            entity_id=created["id"],
            new_value=f"{created['name']} ({created['role']})",
            details=f"Created user {created['email']} for department {created.get('department')}",
            risk_level="MEDIUM",
        )
        return {"success": True, "user": created}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
