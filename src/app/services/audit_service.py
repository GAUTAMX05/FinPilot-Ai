import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime


class AuditLogService:
    def __init__(self):
        self._logs: List[Dict[str, Any]] = []
        self._flags: List[Dict[str, Any]] = []
        self._seed_initial_logs()

    def _seed_initial_logs(self):
        """Initial historical audit logs for compliance tracking."""
        initial_entries = [
            {
                "id": "log_001",
                "user_id": "usr_fm_002",
                "user_name": "Rahul Sharma",
                "role": "FINANCE_MANAGER",
                "action": "BUDGET_UPDATE",
                "entity": "DEPARTMENT_BUDGET",
                "entity_id": "Engineering",
                "old_value": "4,500,000 INR",
                "new_value": "5,000,000 INR",
                "details": "FY26 Q1 Cloud Infrastructure allocation expansion",
                "risk_level": "LOW",
                "timestamp": "2026-08-20T10:15:30Z",
            },
            {
                "id": "log_002",
                "user_id": "usr_cfo_001",
                "user_name": "Vikramaditya Singhania",
                "role": "CFO",
                "action": "FINAL_EXPENSE_APPROVAL",
                "entity": "INVOICE",
                "entity_id": "INV-2026-001",
                "old_value": "PENDING_APPROVAL",
                "new_value": "APPROVED",
                "details": "Authorized Annual AWS Cloud commitment (₹1,85,000.00)",
                "risk_level": "MEDIUM",
                "timestamp": "2026-08-21T14:30:00Z",
            },
            {
                "id": "log_003",
                "user_id": "usr_aud_004",
                "user_name": "Kavita Iyer",
                "role": "AUDITOR",
                "action": "FLAG_TRANSACTION",
                "entity": "INVOICE",
                "entity_id": "INV-2026-004",
                "old_value": "SUBMITTED",
                "new_value": "FLAGGED_FOR_REVIEW",
                "details": "Flagged duplicate invoice submission pattern for SaaS licensing",
                "risk_level": "HIGH",
                "timestamp": "2026-08-22T09:45:12Z",
            },
        ]
        self._logs.extend(initial_entries)

    def log_action(
        self,
        user_id: str,
        user_name: str,
        role: str,
        action: str,
        entity: str,
        entity_id: str,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        details: str = "",
        risk_level: str = "LOW",
    ) -> Dict[str, Any]:
        """Appends an immutable audit log entry."""
        entry = {
            "id": f"log_{uuid.uuid4().hex[:8]}",
            "user_id": user_id,
            "user_name": user_name,
            "role": role,
            "action": action,
            "entity": entity,
            "entity_id": entity_id,
            "old_value": old_value,
            "new_value": new_value,
            "details": details,
            "risk_level": risk_level,
            "timestamp": datetime.now().isoformat(),
        }
        self._logs.insert(0, entry)
        return entry

    def flag_transaction(
        self,
        user_id: str,
        user_name: str,
        role: str,
        entity_id: str,
        reason: str,
        risk_level: str = "HIGH",
    ) -> Dict[str, Any]:
        """Allows Auditor to flag a suspicious transaction without approval/rejection powers."""
        flag_entry = {
            "flag_id": f"flag_{uuid.uuid4().hex[:6]}",
            "entity_id": entity_id,
            "flagged_by_id": user_id,
            "flagged_by_name": user_name,
            "role": role,
            "reason": reason,
            "risk_level": risk_level,
            "status": "OPEN",
            "timestamp": datetime.now().isoformat(),
        }
        self._flags.insert(0, flag_entry)
        self.log_action(
            user_id=user_id,
            user_name=user_name,
            role=role,
            action="FLAG_TRANSACTION",
            entity="INVOICE",
            entity_id=entity_id,
            old_value="ACTIVE",
            new_value="FLAGGED_FOR_REVIEW",
            details=f"Auditor Flagged: {reason}",
            risk_level=risk_level,
        )
        return flag_entry

    def get_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._logs[:limit]

    def get_audit_flags(self) -> List[Dict[str, Any]]:
        return self._flags

    def get_audit_metrics(self) -> Dict[str, Any]:
        """Calculates audit metrics for Auditor and CFO risk dashboards."""
        total_logs = len(self._logs)
        high_risk_count = sum(1 for log in self._logs if log.get("risk_level") in ["HIGH", "CRITICAL"])
        open_flags = sum(1 for flag in self._flags if flag.get("status") == "OPEN")

        return {
            "total_invoices_audited": 128,
            "anomalies_detected": 4,
            "duplicate_invoices": 1,
            "gst_issues": 2,
            "high_risk_transactions": high_risk_count + 1,
            "pending_audit_reviews": open_flags + 2,
            "risk_distribution": {
                "low": 115,
                "medium": 9,
                "high": 3,
                "critical": 1,
            }
        }


audit_service = AuditLogService()
