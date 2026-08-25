from typing import Optional, Callable
from fastapi import Header, HTTPException, Depends
from src.app.core.rbac import Permission, Role, decode_access_token, user_has_permission
from src.app.services.auth_service import auth_service


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Extracts and verifies user from Authorization header (Bearer token)."""
    if not authorization:
        # Default fallback for unauthenticated requests in demo
        cfo_default = auth_service.get_user_by_email("cfo@aifinance.local")
        if cfo_default:
            return cfo_default
        raise HTTPException(status_code=401, detail="Missing Authorization header.")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid authorization scheme. Use Bearer token.")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token.")

    user = auth_service.get_user_by_id(payload.get("id"))
    if not user or not user.get("is_active"):
        raise HTTPException(status_code=401, detail="User account not found or deactivated.")

    return user


def require_permission(permission: Permission) -> Callable:
    """Dependency that enforces a specific permission on an endpoint."""
    async def permission_checker(current_user: dict = Depends(get_current_user)) -> dict:
        role_str = current_user.get("role")
        try:
            role = Role(role_str)
        except ValueError:
            raise HTTPException(status_code=403, detail="Invalid user role assigned.")

        if not user_has_permission(role, permission):
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: Role '{role.value}' does not have '{permission.value}' permission.",
            )
        return current_user

    return permission_checker
