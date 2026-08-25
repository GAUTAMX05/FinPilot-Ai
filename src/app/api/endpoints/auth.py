import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from src.app.services.auth_service import auth_service
from src.app.core.auth_middleware import get_current_user

logger = logging.getLogger("AuthApi")
router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(req: LoginRequest):
    """Authenticates user and returns JWT bearer token and role permissions."""
    res = auth_service.authenticate_user(req.email, req.password)
    if not res:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )
    return {
        "success": True,
        "data": res,
    }


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """Returns currently authenticated user profile and permissions."""
    return {"success": True, "user": current_user}


@router.get("/demo-users")
def get_demo_users():
    """Returns demo accounts for development / testing mode."""
    return {
        "success": True,
        "demo_mode": True,
        "users": auth_service.get_demo_accounts(),
    }
