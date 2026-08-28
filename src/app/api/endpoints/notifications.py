import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.app.core.auth_middleware import get_current_user, require_permission
from src.app.core.rbac import Permission
from src.app.services.notification_service import notification_service
from src.app.services.auth_service import auth_service

logger = logging.getLogger("NotificationsAPI")
router = APIRouter()


class SendNotificationRequest(BaseModel):
    recipient_user_id: str = Field(description="Target recipient user ID (e.g., FIN-MGR-001, ENG-HEAD-001)")
    type: str = Field(default="DIRECT_MESSAGE", description="Notification / Request type")
    title: str = Field(description="Subject line / title")
    message: str = Field(description="Detailed message body")
    priority: str = Field(default="MEDIUM", description="Priority: LOW, MEDIUM, HIGH, CRITICAL")
    entity_type: Optional[str] = Field(default="COMMUNICATION", description="EXPENSE, INVOICE, BUDGET, PAYROLL, ALLOWANCE, RECONCILIATION, AUDIT, COMMUNICATION")
    entity_id: Optional[str] = Field(default="", description="Referenced entity ID")
    department: Optional[str] = Field(default=None, description="Department scope")
    observer_ids: Optional[List[str]] = Field(default_factory=list, description="Observer / CC user IDs")
    action: Optional[str] = Field(default="REVIEW", description="Action tag")


class ReplyNotificationRequest(BaseModel):
    message: str = Field(description="Reply message content")


class ResolveNotificationRequest(BaseModel):
    resolution_note: Optional[str] = Field(default="Reviewed and verified by financial controller.", description="Resolution notes")


class EscalateNotificationRequest(BaseModel):
    escalation_reason: Optional[str] = Field(default="Escalated for CFO executive decision.", description="Escalation reason")


@router.get("")
def get_notifications(
    category: Optional[str] = Query("ALL", description="Notification category/type filter"),
    search: Optional[str] = Query(None, description="Search query string"),
    unread_only: bool = Query(False, description="Filter unread only"),
    current_user: dict = Depends(get_current_user),
):
    """
    STRICT BACKEND ENFORCEMENT:
    Returns ONLY notifications where recipientUserId == authenticatedUser.id
    or authenticatedUser.id is in observerIds.
    Unauthorized notifications are NEVER delivered to the client.
    """
    res = notification_service.get_user_notifications(
        current_user=current_user,
        category=category,
        search=search,
        unread_only=unread_only,
        view="inbox"
    )
    return res


@router.get("/sent")
def get_sent_notifications(
    current_user: dict = Depends(get_current_user),
):
    """Returns requests and notifications initiated by the authenticated user."""
    res = notification_service.get_user_notifications(
        current_user=current_user,
        view="sent"
    )
    return res


@router.get("/directory")
def get_communication_directory(
    current_user: dict = Depends(get_current_user),
):
    """
    Returns the list of recipient users that the authenticated user is permitted
    to communicate with based on enterprise role routing rules.
    """
    directory = auth_service.get_directory_for_user(current_user)
    return {
        "success": True,
        "current_user": {
            "id": current_user["id"],
            "name": current_user["name"],
            "role": current_user["role"],
            "department": current_user.get("department")
        },
        "directory": directory
    }


@router.post("/send")
def send_notification(
    req: SendNotificationRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Creates and dispatches a targeted internal request/notification to an explicit recipient user.
    """
    try:
        notif = notification_service.send_notification(
            sender_user=current_user,
            recipient_user_id=req.recipient_user_id,
            type=req.type,
            title=req.title,
            message=req.message,
            priority=req.priority,
            entity_type=req.entity_type,
            entity_id=req.entity_id,
            department=req.department,
            observer_ids=req.observer_ids,
            action=req.action,
        )
        return {
            "success": True,
            "message": f"Request '{req.title}' sent successfully to {req.recipient_user_id}.",
            "notification": notif
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Failed to dispatch notification")
        raise HTTPException(status_code=500, detail=f"Internal notification error: {str(e)}")


@router.post("/{notification_id}/reply")
def reply_to_notification(
    notification_id: str,
    req: ReplyNotificationRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Adds a reply to an ongoing request thread between sender and recipient.
    """
    try:
        res = notification_service.reply_to_thread(
            notification_id=notification_id,
            sender_user=current_user,
            message=req.message
        )
        return res
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@router.post("/{notification_id}/resolve")
def resolve_notification(
    notification_id: str,
    payload: ResolveNotificationRequest,
    current_user: dict = Depends(get_current_user),
):
    """Resolves an alert / notification with resolution notes and audit logging."""
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


@router.post("/{notification_id}/escalate")
def escalate_notification(
    notification_id: str,
    payload: EscalateNotificationRequest,
    current_user: dict = Depends(get_current_user),
):
    """Escalates an open notification to the CFO for high-level decision."""
    try:
        res = notification_service.escalate_notification(
            notification_id=notification_id,
            user_id=current_user["id"],
            user_name=current_user["name"],
            user_role=current_user["role"],
            escalation_reason=payload.escalation_reason or "",
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{notification_id}/read")
def mark_single_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Marks a single notification as read."""
    return notification_service.mark_as_read(notification_id, current_user["id"])


@router.post("/mark-all-read")
def mark_all_read(current_user: dict = Depends(get_current_user)):
    """Marks all notifications for the authenticated user as read."""
    return notification_service.mark_all_as_read(current_user["id"], current_user.get("role"))


@router.post("/clear")
def clear_all_notifications(current_user: dict = Depends(get_current_user)):
    """Dismisses notifications for the authenticated user."""
    return notification_service.clear_notifications(current_user["id"], current_user.get("role"))


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
