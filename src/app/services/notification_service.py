import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.app.services.audit_service import audit_service

logger = logging.getLogger("NotificationService")


class FinancialNotificationService:
    """
    Enterprise Notification System for Payroll mismatches, Form 16 differences,
    budget overruns, allowance exceptions, and approval escalations.
    """

    def __init__(self):
        self._notifications: List[Dict[str, Any]] = self._init_default_notifications()

    def _init_default_notifications(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "NOTIF-2026-001",
                "category": "PAYROLL",
                "severity": "CRITICAL",
                "title": "Salary Reporting Mismatch",
                "employee_id": "EMP-1042",
                "employee_name": "Siddharth Verma",
                "department": "Engineering",
                "payroll_salary": 840000.0,
                "form16_salary": 875000.0,
                "difference": 35000.0,
                "summary": "Payroll salary (₹8,40,000) differs from Form 16 reported gross (₹8,75,000) by ₹35,000. Verification required before quarterly tax filing.",
                "status": "UNRESOLVED",
                "created_at": "2026-08-23T20:15:00",
                "recommended_action": "Review salary components and adjust Form 16 Annexure B classification.",
                "actions": ["REVIEW", "RESOLVE", "NOTIFY_FINANCE"],
            },
            {
                "id": "NOTIF-2026-002",
                "category": "COMPLIANCE",
                "severity": "WARNING",
                "title": "Tax Reporting Review (TDS Variance)",
                "employee_id": "EMP-1088",
                "employee_name": "Rohan Malhotra",
                "department": "Marketing",
                "payroll_salary": 960000.0,
                "form16_salary": 960000.0,
                "difference": 0.0,
                "summary": "Payroll TDS (₹1,44,000) does not match Form 26AS deposit credit (₹1,32,000). ₹12,000 challan credit missing in TRACES.",
                "status": "UNRESOLVED",
                "created_at": "2026-08-23T19:40:00",
                "recommended_action": "Verify bank challan CIN for June 2026 deposit.",
                "actions": ["REVIEW", "RESOLVE", "NOTIFY_FINANCE"],
            },
            {
                "id": "NOTIF-2026-003",
                "category": "COMPLIANCE",
                "severity": "REVIEW",
                "title": "Missing Form 16 Tax Document",
                "employee_id": "EMP-1091",
                "employee_name": "Ananya Joshi",
                "department": "Sales",
                "payroll_salary": 1120000.0,
                "form16_salary": 0.0,
                "difference": 1120000.0,
                "summary": "Form 16 certificate has not been uploaded for reporting period FY 2026–27 (AY 2027–28).",
                "status": "UNRESOLVED",
                "created_at": "2026-08-23T18:30:00",
                "recommended_action": "Request signed Form 16 Part A & Part B from payroll vendor.",
                "actions": ["REVIEW", "REQUEST_UPLOAD", "RESOLVE"],
            },
            {
                "id": "NOTIF-2026-004",
                "category": "FINANCIAL",
                "severity": "CRITICAL",
                "title": "Engineering Projected Budget Overrun",
                "employee_id": "DEPT-ENG",
                "employee_name": "Engineering Department",
                "department": "Engineering",
                "payroll_salary": 0.0,
                "form16_salary": 0.0,
                "difference": 420000.0,
                "summary": "Engineering spending velocity (₹370,000/mo) is projected to exceed annual budget by ₹420,000.",
                "status": "UNRESOLVED",
                "created_at": "2026-08-23T17:00:00",
                "recommended_action": "Execute recommended budget reallocation from Operations surplus.",
                "actions": ["VIEW_DECISION", "RESOLVE"],
            },
            {
                "id": "NOTIF-2026-005",
                "category": "EMPLOYEE",
                "severity": "WARNING",
                "title": "Employee Allowance Limit Exceeded",
                "employee_id": "EMP-101",
                "employee_name": "Rahul Sharma",
                "department": "Engineering",
                "payroll_salary": 0.0,
                "form16_salary": 0.0,
                "difference": 64000.0,
                "summary": "Monthly travel claims (₹24,800) exceed configured department allowance cap of ₹15,000.",
                "status": "UNRESOLVED",
                "created_at": "2026-08-23T16:15:00",
                "recommended_action": "Review claims CLM-991 & CLM-994 for policy exception approval.",
                "actions": ["REVIEW_EXCEPTION", "RESOLVE"],
            },
            {
                "id": "NOTIF-2026-006",
                "category": "APPROVALS",
                "severity": "WARNING",
                "title": "Manager Authorization Required (>= ₹50,000)",
                "employee_id": "INV-2026-001",
                "employee_name": "CloudOps Technologies",
                "department": "Engineering",
                "payroll_salary": 0.0,
                "form16_salary": 0.0,
                "difference": 100300.0,
                "summary": "Invoice INV-2026-001 (₹100,300) requires Human-in-the-Loop manager authorization under governance policy.",
                "status": "UNRESOLVED",
                "created_at": "2026-08-23T15:00:00",
                "recommended_action": "Review affordability simulation and approve or reject disbursement.",
                "actions": ["REVIEW_APPROVAL", "RESOLVE"],
            }
        ]

    def create_notification(
        self,
        category: str = "FINANCIAL",
        severity: str = "CRITICAL",
        title: str = "Financial Alert",
        summary: str = "",
        message: Optional[str] = None,
        notification_type: Optional[str] = None,
        entity_id: str = "",
        department: str = "Engineering",
        recommended_action: str = ""
    ) -> Dict[str, Any]:
        import uuid
        notif = {
            "id": f"NOTIF-{datetime.utcnow().strftime('%Y')}-{uuid.uuid4().hex[:4].upper()}",
            "category": category,
            "severity": severity,
            "title": title,
            "employee_id": entity_id,
            "employee_name": f"{department} Controller",
            "department": department,
            "payroll_salary": 0.0,
            "form16_salary": 0.0,
            "difference": 0.0,
            "summary": summary or message or title,
            "status": "UNRESOLVED",
            "created_at": datetime.utcnow().isoformat(),
            "recommended_action": recommended_action or "Review policy exception.",
            "actions": ["REVIEW", "RESOLVE"]
        }
        self._notifications.insert(0, notif)
        return notif

    def get_notifications(
        self,
        category: Optional[str] = None,
        user_role: Optional[str] = None,
        user_department: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Returns filtered active notifications based on role and category."""
        notifs = [n for n in self._notifications if n.get("status") != "DISMISSED"]

        # Department Head visibility filter
        if user_role == "DEPARTMENT_HEAD" and user_department:
            notifs = [n for n in notifs if n.get("department", "").lower() == user_department.lower()]

        if category and category.upper() != "ALL":
            notifs = [n for n in notifs if n.get("category", "").upper() == category.upper()]

        unresolved_count = sum(1 for n in notifs if n.get("status") == "UNRESOLVED")

        return {
            "success": True,
            "total": len(notifs),
            "unresolved_count": unresolved_count,
            "notifications": notifs,
        }

    def resolve_notification(
        self,
        notification_id: str,
        user_id: str,
        user_name: str,
        user_role: str,
        resolution_note: str = "",
    ) -> Dict[str, Any]:
        """Resolves a notification, logs the resolution note, and commits to the audit trail."""
        for n in self._notifications:
            if n["id"] == notification_id:
                n["status"] = "RESOLVED"
                n["resolved_by"] = user_name
                n["resolved_by_role"] = user_role
                n["resolved_at"] = datetime.now().isoformat()
                n["resolution_note"] = resolution_note or "Reviewed and verified by finance controller."

                # Log to audit trail
                audit_service.log_action(
                    user_id=user_id,
                    user_name=user_name,
                    role=user_role,
                    action="RESOLVE_NOTIFICATION",
                    entity="NOTIFICATION",
                    entity_id=notification_id,
                    new_value="RESOLVED",
                    details=f"Notification '{n['title']}' for {n['employee_name']} resolved. Note: {n['resolution_note']}",
                    risk_level="LOW",
                )

                return {
                    "success": True,
                    "message": f"Notification '{n['title']}' marked as Resolved.",
                    "notification": n,
                }

        raise ValueError(f"Notification '{notification_id}' not found.")

    def notify_finance_team(
        self,
        notification_id: str,
        user_name: str,
        user_role: str,
    ) -> Dict[str, Any]:
        """Dispatches an internal alert to the finance and tax operations team."""
        for n in self._notifications:
            if n["id"] == notification_id:
                n["finance_notified"] = True
                n["finance_notified_at"] = datetime.now().isoformat()
                n["finance_notified_by"] = user_name

                audit_service.log_action(
                    user_id="SYSTEM",
                    user_name=user_name,
                    role=user_role,
                    action="NOTIFY_FINANCE_TEAM",
                    entity="NOTIFICATION",
                    entity_id=notification_id,
                    details=f"Dispatched compliance notification to Central Finance Operations for {n['title']} ({n['employee_name']}).",
                    risk_level="LOW",
                )

                return {
                    "success": True,
                    "message": f"Central Finance Team notified for {n['title']}.",
                    "notification": n,
                }

        raise ValueError(f"Notification '{notification_id}' not found.")

    def mark_all_as_read(self, user_name: str, user_role: str) -> Dict[str, Any]:
        for n in self._notifications:
            if n.get("status") == "UNRESOLVED":
                n["status"] = "READ"
        return {"success": True, "message": "All notifications marked as read."}

    def clear_notifications(self, user_name: str, user_role: str) -> Dict[str, Any]:
        for n in self._notifications:
            n["status"] = "DISMISSED"
        return {"success": True, "message": "Notifications cleared."}


notification_service = FinancialNotificationService()
