import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.app.core.auth_middleware import get_current_user, require_permission
from src.app.core.rbac import Permission
from src.app.services.notification_service import notification_service

logger = logging.getLogger("NotificationsAPI")
router = APIRouter()


class ResolveNotificationRequest(BaseModel):
    resolution_note: Optional[str] = "Resolved by financial controller."


@router.get("")
def get_notifications(
    category: Optional[str] = Query("ALL", description="Notification category filter"),
    current_user: dict = Depends(get_current_user),
):
    """Retrieves filtered notifications."""
    res = notification_service.get_notifications(
        category=category,
        user_role=current_user["role"],
        user_department=current_user.get("department"),
    )
    return res


@router.post("/{notification_id}/resolve")
def resolve_notification(
    notification_id: str,
    payload: ResolveNotificationRequest,
    current_user: dict = Depends(require_permission(Permission.APPROVE_EXPENSE)),
):
    """Resolves an alert / notification with resolution notes."""
    try:
        res = notification_service.resolve_notification(
            notification_id=notification_id,
            user_id=current_user["id"],
            user_name=current_user["name"],
            user_role=current_user["role"],
            resolution_note=payload.resolution_note or "",
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{notification_id}/notify-finance")
def notify_finance_team(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Alerts Central Finance Operations regarding a reporting or tax difference."""
    try:
        res = notification_service.notify_finance_team(
            notification_id=notification_id,
            user_name=current_user["name"],
            user_role=current_user["role"],
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/mark-all-read")
def mark_all_read(current_user: dict = Depends(get_current_user)):
    return notification_service.mark_all_as_read(current_user["name"], current_user["role"])


@router.post("/clear")
def clear_all_notifications(current_user: dict = Depends(get_current_user)):
    return notification_service.clear_notifications(current_user["name"], current_user["role"])
