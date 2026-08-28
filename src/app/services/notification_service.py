import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.app.core.rbac import Role
from src.app.services.audit_service import audit_service

logger = logging.getLogger("NotificationService")

# Supported Notification Types
NOTIFICATION_TYPES = {
    "APPROVAL_REQUEST",
    "APPROVAL_RESPONSE",
    "BUDGET_WARNING",
    "BUDGET_REQUEST",
    "INVOICE_REVIEW",
    "INVOICE_ANOMALY",
    "RECONCILIATION_EXCEPTION",
    "PAYROLL_MISMATCH",
    "FORM16_MISMATCH",
    "ALLOWANCE_EXCEPTION",
    "COMPLIANCE_ALERT",
    "AUDIT_ASSIGNMENT",
    "DIRECT_MESSAGE",
    "SYSTEM_ALERT",
    "DECISION_REQUEST",
    "ESCALATION",
}

# Priority Levels
PRIORITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

# Entity Types
ENTITY_TYPES = {"EXPENSE", "INVOICE", "BUDGET", "PAYROLL", "ALLOWANCE", "RECONCILIATION", "AUDIT", "COMMUNICATION"}

# Tab Mappings for Instant Navigation
TAB_MAPPINGS = {
    "APPROVAL_REQUEST": "approvals",
    "APPROVAL_RESPONSE": "approvals",
    "DECISION_REQUEST": "approvals",
    "ESCALATION": "approvals",
    "BUDGET_WARNING": "budgets",
    "BUDGET_REQUEST": "budgets",
    "INVOICE_REVIEW": "invoices",
    "INVOICE_ANOMALY": "invoices",
    "RECONCILIATION_EXCEPTION": "reconciliation",
    "PAYROLL_MISMATCH": "taxreporting",
    "FORM16_MISMATCH": "taxreporting",
    "ALLOWANCE_EXCEPTION": "allowances",
    "COMPLIANCE_ALERT": "audit",
    "AUDIT_ASSIGNMENT": "audit",
    "DIRECT_MESSAGE": "dashboard",
    "SYSTEM_ALERT": "dashboard",
}


class FinancialNotificationService:
    """
    Enterprise Role-Based Notification & Internal Communication System.
    Strictly guarantees that every notification is delivered ONLY to authorized
    recipient users (no global feed leakage, department scope isolation,
    and two-way conversation threading).
    """

    def __init__(self):
        self._notifications: List[Dict[str, Any]] = self._init_default_notifications()

    def _init_default_notifications(self) -> List[Dict[str, Any]]:
        """Initializes realistic enterprise notifications targeted to specific demo users."""
        return [
            # 1. Targeted to Finance Manager (Rahul Verma, FIN-MGR-001) from CFO
            {
                "id": "NTF-1029",
                "recipientUserId": "FIN-MGR-001",
                "senderUserId": "CFO-001",
                "senderName": "Vikramaditya Singhania",
                "senderRole": "CFO",
                "recipientRole": "FINANCE_MANAGER",
                "department": "Engineering",
                "type": "APPROVAL_REQUEST",
                "title": "Approval Required: High-Value Cloud Expense",
                "message": "Please review the ₹85,000 Engineering cloud infrastructure expense submitted for Q3 expansion.",
                "priority": "HIGH",
                "entityType": "EXPENSE",
                "entityId": "EXP-1021",
                "action": "REVIEW_APPROVAL",
                "actionTab": "approvals",
                "isRead": False,
                "observerIds": ["AUDITOR-001"],
                "thread": [
                    {
                        "senderUserId": "CFO-001",
                        "senderName": "Vikramaditya Singhania",
                        "senderRole": "CFO",
                        "message": "Please review the ₹85,000 Engineering cloud expense before executive sign-off.",
                        "timestamp": "2026-08-28T10:15:00"
                    }
                ],
                "status": "OPEN",
                "createdAt": "2026-08-28T10:15:00",
                "updatedAt": "2026-08-28T10:15:00",
                # Backwards compatible aliases
                "category": "APPROVALS",
                "severity": "HIGH",
                "summary": "Please review the ₹85,000 Engineering cloud infrastructure expense submitted for Q3 expansion.",
                "recommended_action": "Review affordability simulation and approve or reject disbursement."
            },

            # 2. Targeted to CFO (Vikramaditya Singhania, CFO-001) from Finance Manager
            {
                "id": "NTF-1030",
                "recipientUserId": "CFO-001",
                "senderUserId": "FIN-MGR-001",
                "senderName": "Rahul Verma",
                "senderRole": "FINANCE_MANAGER",
                "recipientRole": "CFO",
                "department": "Engineering",
                "type": "DECISION_REQUEST",
                "title": "Budget Reallocation Decision Required",
                "message": "Engineering is projected to exceed its annual budget by ₹420,000. Reallocation of ₹250,000 from Operations surplus is recommended.",
                "priority": "HIGH",
                "entityType": "BUDGET",
                "entityId": "DEPT-ENG",
                "action": "VIEW_DECISION",
                "actionTab": "budgets",
                "isRead": False,
                "observerIds": [],
                "thread": [
                    {
                        "senderUserId": "FIN-MGR-001",
                        "senderName": "Rahul Verma",
                        "senderRole": "FINANCE_MANAGER",
                        "message": "Engineering projected budget overrun requires your executive sign-off for surplus transfer.",
                        "timestamp": "2026-08-28T09:30:00"
                    }
                ],
                "status": "OPEN",
                "createdAt": "2026-08-28T09:30:00",
                "updatedAt": "2026-08-28T09:30:00",
                "category": "FINANCIAL",
                "severity": "CRITICAL",
                "summary": "Engineering spending velocity (₹370,000/mo) is projected to exceed annual budget by ₹420,000.",
                "recommended_action": "Execute recommended budget reallocation from Operations surplus."
            },

            # 3. Targeted ONLY to Engineering Dept Head (Arjun Mehta, ENG-HEAD-001) from Finance Manager
            {
                "id": "NTF-1031",
                "recipientUserId": "ENG-HEAD-001",
                "senderUserId": "FIN-MGR-001",
                "senderName": "Rahul Verma",
                "senderRole": "FINANCE_MANAGER",
                "recipientRole": "DEPARTMENT_HEAD",
                "department": "Engineering",
                "type": "BUDGET_WARNING",
                "title": "Engineering Budget Threshold Alert (82%)",
                "message": "Engineering department spend has reached 82.4% of allocated annual pool with 4 months remaining in FY.",
                "priority": "MEDIUM",
                "entityType": "BUDGET",
                "entityId": "DEPT-ENG",
                "action": "REVIEW_BUDGET",
                "actionTab": "budgets",
                "isRead": False,
                "observerIds": [],
                "thread": [
                    {
                        "senderUserId": "FIN-MGR-001",
                        "senderName": "Rahul Verma",
                        "senderRole": "FINANCE_MANAGER",
                        "message": "Please review your Q4 projected run-rate and provide spend justification.",
                        "timestamp": "2026-08-28T08:45:00"
                    }
                ],
                "status": "OPEN",
                "createdAt": "2026-08-28T08:45:00",
                "updatedAt": "2026-08-28T08:45:00",
                "category": "FINANCIAL",
                "severity": "WARNING",
                "summary": "Engineering budget utilization has reached 82.4%.",
                "recommended_action": "Review department expense commitments."
            },

            # 4. Targeted ONLY to Auditor (Kavita Iyer, AUDITOR-001)
            {
                "id": "NTF-1032",
                "recipientUserId": "AUDITOR-001",
                "senderUserId": "FIN-MGR-001",
                "senderName": "Rahul Verma",
                "senderRole": "FINANCE_MANAGER",
                "recipientRole": "AUDITOR",
                "department": None,
                "type": "INVOICE_ANOMALY",
                "title": "Audit Review Required: Invoice Anomaly Detected",
                "message": "Invoice INV-2026-004 from CloudOps Technologies triggered duplicate submission heuristic with INV-2026-001.",
                "priority": "CRITICAL",
                "entityType": "INVOICE",
                "entityId": "INV-2026-004",
                "action": "AUDIT_INVOICE",
                "actionTab": "invoices",
                "isRead": False,
                "observerIds": ["CFO-001"],
                "thread": [
                    {
                        "senderUserId": "FIN-MGR-001",
                        "senderName": "Rahul Verma",
                        "senderRole": "FINANCE_MANAGER",
                        "message": "Assigned for independent audit compliance verification.",
                        "timestamp": "2026-08-28T08:00:00"
                    }
                ],
                "status": "OPEN",
                "createdAt": "2026-08-28T08:00:00",
                "updatedAt": "2026-08-28T08:00:00",
                "category": "COMPLIANCE",
                "severity": "CRITICAL",
                "summary": "Potential duplicate invoice detected for CloudOps Technologies.",
                "recommended_action": "Inspect tax invoice hash and vendor GSTIN."
            },

            # 5. Sensitive Tax / Form 16 Mismatch targeted to Finance Manager (FIN-MGR-001)
            {
                "id": "NTF-1033",
                "recipientUserId": "FIN-MGR-001",
                "senderUserId": "SYSTEM",
                "senderName": "Automated Tax Reconciler",
                "senderRole": "SYSTEM",
                "recipientRole": "FINANCE_MANAGER",
                "department": "Engineering",
                "type": "FORM16_MISMATCH",
                "title": "Form 16 vs Payroll Reporting Discrepancy",
                "message": "Employee EMP-1042 (Siddharth Verma) has a ₹35,000 discrepancy between Payroll gross salary and Form 16 Annexure B.",
                "priority": "CRITICAL",
                "entityType": "PAYROLL",
                "entityId": "EMP-1042",
                "action": "RECONCILE_TAX",
                "actionTab": "taxreporting",
                "isRead": False,
                "observerIds": ["CFO-001", "AUDITOR-001"],
                "thread": [],
                "status": "OPEN",
                "createdAt": "2026-08-28T07:30:00",
                "updatedAt": "2026-08-28T07:30:00",
                "category": "PAYROLL",
                "severity": "CRITICAL",
                "summary": "Payroll gross salary differs from Form 16 reported gross by ₹35,000.",
                "recommended_action": "Verify Form 16 Part B Annexure."
            }
        ]

    def _match_user_id(self, target_id: Optional[str], candidate_id: Optional[str]) -> bool:
        """Helper to match user IDs taking aliases (e.g. CFO-001 vs usr_cfo_001) into account."""
        if not target_id or not candidate_id:
            return False
        t = target_id.strip().upper()
        c = candidate_id.strip().upper()
        if t == c:
            return True
            
        aliases_map = {
            "CFO-001": {"USR_CFO_001", "CFO", "CFO@AIFINANCE.LOCAL"},
            "FIN-MGR-001": {"USR_FM_002", "FM", "FINANCEMANAGER", "FINANCE.MANAGER@AIFINANCE.LOCAL"},
            "ENG-HEAD-001": {"USR_DH_003", "DEPTHEAD", "HEAD", "ENGINEERING.HEAD@AIFINANCE.LOCAL"},
            "MKT-HEAD-001": {"MKT_HEAD", "MARKETING.HEAD@AIFINANCE.LOCAL"},
            "SALES-HEAD-001": {"SALES_HEAD", "SALES.HEAD@AIFINANCE.LOCAL"},
            "HR-HEAD-001": {"HR_HEAD", "HR.HEAD@AIFINANCE.LOCAL"},
            "AUDITOR-001": {"USR_AUD_004", "AUDITOR", "AUDITOR@AIFINANCE.LOCAL"},
        }
        
        for k, v in aliases_map.items():
            all_k = {k} | v
            if t in all_k and c in all_k:
                return True
        return False

    def get_user_notifications(
        self,
        current_user: Dict[str, Any],
        category: Optional[str] = "ALL",
        search: Optional[str] = None,
        unread_only: bool = False,
        view: str = "inbox",
    ) -> Dict[str, Any]:
        """
        STRICT BACKEND SECURITY:
        Returns notifications belonging ONLY to the authenticated user.
        - Inbox: recipientUserId == current_user.id OR current_user.id in observerIds
        - Sent: senderUserId == current_user.id
        - Sensitive Check: Payroll/Form 16 only visible to authorized financial roles.
        - Department Scope: Department Heads can only see their department.
        """
        user_id = current_user.get("id", "")
        user_role = current_user.get("role", "")
        user_dept = current_user.get("department")

        filtered = []
        for n in self._notifications:
            if n.get("status") == "DISMISSED":
                continue

            # 1. User Identity Match (Recipient / Observer vs Sent)
            if view == "sent":
                if not self._match_user_id(n.get("senderUserId"), user_id):
                    continue
            else:
                # Inbox mode
                is_recipient = self._match_user_id(n.get("recipientUserId"), user_id)
                is_observer = any(self._match_user_id(obs, user_id) for obs in n.get("observerIds", []))
                if not (is_recipient or is_observer):
                    continue

            # 2. Sensitive Notification Access Check
            is_sensitive = (
                n.get("entityType") == "PAYROLL"
                or n.get("type") in ["FORM16_MISMATCH", "PAYROLL_MISMATCH"]
                or n.get("category") == "PAYROLL"
            )
            if is_sensitive:
                if user_role not in [Role.CFO.value, Role.FINANCE_MANAGER.value, Role.AUDITOR.value]:
                    continue

            # 3. Department Scope Isolation for Department Heads
            if user_role == Role.DEPARTMENT_HEAD.value and user_dept:
                notif_dept = n.get("department")
                if notif_dept and notif_dept.strip().lower() != user_dept.strip().lower():
                    continue

            # 4. Category / Type Filter
            if category and category.upper() != "ALL":
                c_up = category.upper()
                match_cat = (
                    n.get("category", "").upper() == c_up
                    or n.get("type", "").upper() == c_up
                    or n.get("entityType", "").upper() == c_up
                )
                if not match_cat:
                    continue

            # 5. Unread Filter
            if unread_only and n.get("isRead"):
                continue

            # 6. Search Query Filter
            if search:
                s_low = search.strip().lower()
                title_m = s_low in n.get("title", "").lower()
                msg_m = s_low in n.get("message", "").lower()
                ent_m = s_low in n.get("entityId", "").lower()
                sender_m = s_low in n.get("senderName", "").lower()
                if not (title_m or msg_m or ent_m or sender_m):
                    continue

            filtered.append(n)

        unread_count = sum(1 for n in filtered if not n.get("isRead"))
        unresolved_count = sum(1 for n in filtered if n.get("status") in ["OPEN", "ESCALATED"])

        return {
            "success": True,
            "total": len(filtered),
            "unread_count": unread_count,
            "unresolved_count": unresolved_count,
            "notifications": filtered,
        }

    def send_notification(
        self,
        sender_user: Dict[str, Any],
        recipient_user_id: str,
        type: str,
        title: str,
        message: str,
        priority: str = "MEDIUM",
        entity_type: Optional[str] = "COMMUNICATION",
        entity_id: Optional[str] = "",
        department: Optional[str] = None,
        observer_ids: Optional[List[str]] = None,
        action: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Creates and sends a targeted notification/request to a specific recipient user.
        Logs audit trail action.
        """
        from src.app.services.auth_service import auth_service

        recip_user = auth_service.get_user_by_id(recipient_user_id)
        if not recip_user:
            raise ValueError(f"Recipient user '{recipient_user_id}' not found in user directory.")

        notif_id = f"NTF-{datetime.utcnow().strftime('%Y')}-{uuid.uuid4().hex[:4].upper()}"
        act_tab = TAB_MAPPINGS.get(type, "dashboard")
        now_str = datetime.utcnow().isoformat()

        notif = {
            "id": notif_id,
            "recipientUserId": recip_user["id"],
            "senderUserId": sender_user["id"],
            "senderName": sender_user["name"],
            "senderRole": sender_user["role"],
            "recipientRole": recip_user["role"],
            "department": department or recip_user.get("department") or sender_user.get("department"),
            "type": type if type in NOTIFICATION_TYPES else "DIRECT_MESSAGE",
            "title": title,
            "message": message,
            "priority": priority if priority in PRIORITIES else "MEDIUM",
            "entityType": entity_type if entity_type in ENTITY_TYPES else "COMMUNICATION",
            "entityId": entity_id or "",
            "action": action or "REVIEW",
            "actionTab": act_tab,
            "isRead": False,
            "observerIds": observer_ids or [],
            "thread": [
                {
                    "senderUserId": sender_user["id"],
                    "senderName": sender_user["name"],
                    "senderRole": sender_user["role"],
                    "message": message,
                    "timestamp": now_str
                }
            ],
            "status": "OPEN",
            "createdAt": now_str,
            "updatedAt": now_str,
            # Backwards compatible fields
            "category": entity_type or "FINANCIAL",
            "severity": priority,
            "summary": message,
            "recommended_action": f"Review {title}",
            "actions": ["REVIEW", "RESOLVE"]
        }

        self._notifications.insert(0, notif)

        # Audit Logging
        audit_service.log_action(
            user_id=sender_user["id"],
            user_name=sender_user["name"],
            role=sender_user["role"],
            action="SEND_INTERNAL_REQUEST",
            entity="NOTIFICATION",
            entity_id=notif_id,
            details=f"Sent {type} ('{title}') to {recip_user['name']} ({recip_user['id']}) regarding {entity_type} {entity_id}.",
            risk_level="LOW" if priority in ["LOW", "MEDIUM"] else "HIGH",
        )

        return notif

    def reply_to_thread(
        self,
        notification_id: str,
        sender_user: Dict[str, Any],
        message: str,
    ) -> Dict[str, Any]:
        """
        Appends a reply message to a notification conversation thread.
        Notifies recipient and logs audit record.
        """
        for n in self._notifications:
            if n["id"] == notification_id:
                sender_id = sender_user["id"]
                is_party = (
                    self._match_user_id(n.get("recipientUserId"), sender_id)
                    or self._match_user_id(n.get("senderUserId"), sender_id)
                    or any(self._match_user_id(obs, sender_id) for obs in n.get("observerIds", []))
                )
                if not is_party and sender_user.get("role") != Role.CFO.value:
                    raise PermissionError("Unauthorized: You are not a participant in this conversation thread.")

                now_str = datetime.utcnow().isoformat()
                reply_entry = {
                    "senderUserId": sender_user["id"],
                    "senderName": sender_user["name"],
                    "senderRole": sender_user["role"],
                    "message": message,
                    "timestamp": now_str
                }
                n.setdefault("thread", []).append(reply_entry)
                n["updatedAt"] = now_str
                n["isRead"] = False # Unread for the counterparty

                # Log to audit trail
                audit_service.log_action(
                    user_id=sender_user["id"],
                    user_name=sender_user["name"],
                    role=sender_user["role"],
                    action="REPLY_NOTIFICATION_THREAD",
                    entity="NOTIFICATION",
                    entity_id=notification_id,
                    details=f"Replied to thread '{n['title']}': '{message[:60]}...'",
                    risk_level="LOW",
                )

                return {
                    "success": True,
                    "message": "Reply posted successfully.",
                    "thread": n["thread"],
                    "notification": n
                }

        raise ValueError(f"Notification '{notification_id}' not found.")

    def resolve_notification(
        self,
        notification_id: str,
        user_id: str,
        user_name: str,
        user_role: str,
        resolution_note: str = "",
    ) -> Dict[str, Any]:
        """Marks notification as resolved and appends resolution note to thread."""
        for n in self._notifications:
            if n["id"] == notification_id:
                now_str = datetime.utcnow().isoformat()
                n["status"] = "RESOLVED"
                n["isRead"] = True
                n["resolved_by"] = user_name
                n["resolved_by_role"] = user_role
                n["resolved_at"] = now_str
                n["resolution_note"] = resolution_note or "Reviewed and marked resolved."
                n["updatedAt"] = now_str

                n.setdefault("thread", []).append({
                    "senderUserId": user_id,
                    "senderName": user_name,
                    "senderRole": user_role,
                    "message": f"✅ Resolution Note: {n['resolution_note']}",
                    "timestamp": now_str
                })

                audit_service.log_action(
                    user_id=user_id,
                    user_name=user_name,
                    role=user_role,
                    action="RESOLVE_NOTIFICATION",
                    entity="NOTIFICATION",
                    entity_id=notification_id,
                    new_value="RESOLVED",
                    details=f"Notification '{n['title']}' marked resolved by {user_name}. Note: {n['resolution_note']}",
                    risk_level="LOW",
                )

                return {
                    "success": True,
                    "message": f"Notification '{n['title']}' marked as Resolved.",
                    "notification": n,
                }

        raise ValueError(f"Notification '{notification_id}' not found.")

    def escalate_notification(
        self,
        notification_id: str,
        user_id: str,
        user_name: str,
        user_role: str,
        escalation_reason: str = "",
    ) -> Dict[str, Any]:
        """Escalates notification to CFO (CFO-001) for executive decision."""
        for n in self._notifications:
            if n["id"] == notification_id:
                now_str = datetime.utcnow().isoformat()
                old_recip = n.get("recipientUserId")
                n["recipientUserId"] = "CFO-001"
                n["recipientRole"] = "CFO"
                n["priority"] = "CRITICAL"
                n["status"] = "ESCALATED"
                n["isRead"] = False
                n["updatedAt"] = now_str

                n.setdefault("thread", []).append({
                    "senderUserId": user_id,
                    "senderName": user_name,
                    "senderRole": user_role,
                    "message": f"🚨 ESCALATION TO CFO: {escalation_reason or 'Escalated for executive review and sign-off.'}",
                    "timestamp": now_str
                })

                audit_service.log_action(
                    user_id=user_id,
                    user_name=user_name,
                    role=user_role,
                    action="ESCALATE_NOTIFICATION",
                    entity="NOTIFICATION",
                    entity_id=notification_id,
                    details=f"Escalated notification '{n['title']}' from {old_recip} to CFO-001. Reason: {escalation_reason}",
                    risk_level="HIGH",
                )

                return {
                    "success": True,
                    "message": f"Notification '{n['title']}' escalated to CFO.",
                    "notification": n,
                }

        raise ValueError(f"Notification '{notification_id}' not found.")

    def mark_as_read(self, notification_id: str, user_id: str) -> Dict[str, Any]:
        for n in self._notifications:
            if n["id"] == notification_id:
                if self._match_user_id(n.get("recipientUserId"), user_id) or any(self._match_user_id(obs, user_id) for obs in n.get("observerIds", [])):
                    n["isRead"] = True
                    n["updatedAt"] = datetime.utcnow().isoformat()
                    return {"success": True, "message": "Notification marked as read."}
        return {"success": True, "message": "Notification updated."}

    def mark_all_as_read(self, user_id: str, user_role: Optional[str] = None) -> Dict[str, Any]:
        count = 0
        now_str = datetime.utcnow().isoformat()
        for n in self._notifications:
            if self._match_user_id(n.get("recipientUserId"), user_id) or any(self._match_user_id(obs, user_id) for obs in n.get("observerIds", [])):
                n["isRead"] = True
                n["updatedAt"] = now_str
                count += 1
        return {"success": True, "message": f"{count} notifications marked as read."}

    def clear_notifications(self, user_id: str, user_role: Optional[str] = None) -> Dict[str, Any]:
        for n in self._notifications:
            if self._match_user_id(n.get("recipientUserId"), user_id):
                n["status"] = "DISMISSED"
        return {"success": True, "message": "Notifications dismissed."}

    # Compatibility method for legacy calls
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
        recommended_action: str = "",
        recipient_user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Default routing logic if recipient is not explicitly provided:
        if not recipient_user_id:
            if category == "APPROVALS" or severity == "CRITICAL":
                recipient_user_id = "FIN-MGR-001"
            elif category == "EMPLOYEE" or department == "Engineering":
                recipient_user_id = "ENG-HEAD-001"
            elif category == "COMPLIANCE":
                recipient_user_id = "AUDITOR-001"
            else:
                recipient_user_id = "CFO-001"

        sender_user = {
            "id": "SYSTEM",
            "name": "System Controller",
            "role": "SYSTEM",
            "department": department
        }

        return self.send_notification(
            sender_user=sender_user,
            recipient_user_id=recipient_user_id,
            type=notification_type or ("APPROVAL_REQUEST" if category == "APPROVALS" else "BUDGET_WARNING"),
            title=title,
            message=message or summary or title,
            priority="CRITICAL" if severity == "CRITICAL" else ("HIGH" if severity in ["HIGH", "WARNING"] else "MEDIUM"),
            entity_type=category or "FINANCIAL",
            entity_id=entity_id,
            department=department,
            action="REVIEW",
        )

    def get_notifications(
        self,
        category: Optional[str] = None,
        user_role: Optional[str] = None,
        user_department: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Compatibility wrapper for endpoints passing role/dept
        user_id = "CFO-001"
        if user_role == "FINANCE_MANAGER":
            user_id = "FIN-MGR-001"
        elif user_role == "DEPARTMENT_HEAD":
            user_id = "ENG-HEAD-001" if user_department == "Engineering" else "MKT-HEAD-001"
        elif user_role == "AUDITOR":
            user_id = "AUDITOR-001"

        current_user = {
            "id": user_id,
            "role": user_role or "CFO",
            "department": user_department
        }
        return self.get_user_notifications(current_user, category=category)

    def notify_finance_team(
        self,
        notification_id: str,
        user_name: str,
        user_role: str,
    ) -> Dict[str, Any]:
        for n in self._notifications:
            if n["id"] == notification_id:
                now_str = datetime.utcnow().isoformat()
                n.setdefault("observerIds", [])
                if "FIN-MGR-001" not in n["observerIds"]:
                    n["observerIds"].append("FIN-MGR-001")
                n.setdefault("thread", []).append({
                    "senderUserId": "SYSTEM",
                    "senderName": user_name,
                    "senderRole": user_role,
                    "message": f"📢 Dispatched alert to Central Finance Operations Team by {user_name}.",
                    "timestamp": now_str
                })
                return {
                    "success": True,
                    "message": f"Central Finance Team notified for {n['title']}.",
                    "notification": n,
                }
        raise ValueError(f"Notification '{notification_id}' not found.")


notification_service = FinancialNotificationService()
