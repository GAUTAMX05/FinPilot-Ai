import hashlib
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime


class AuditLogService:
    def __init__(self):
        self._logs: List[Dict[str, Any]] = []
        self._flags: List[Dict[str, Any]] = []
        self._last_hash = "GENESIS_BLOCK_000000000000000000000000000000000000000000000000000000"
        self._seed_initial_logs()

    def _generate_hash(self, payload: str, prev_hash: str) -> str:
        """Generates SHA-256 hash for immutable chaining."""
        raw = f"{prev_hash}|{payload}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _seed_initial_logs(self):
        """Initial historical audit logs for compliance tracking."""
        initial_entries = [
            ("usr_fm_002", "Rahul Verma", "FINANCE_MANAGER", "BUDGET_UPDATE", "DEPARTMENT_BUDGET", "Engineering", "4,500,000 INR", "5,000,000 INR", "FY26 Q1 Cloud Infrastructure allocation expansion", "LOW", "2026-08-15T09:15:30Z"),
            ("usr_cfo_001", "Vikramaditya Singhania", "CFO", "FINAL_EXPENSE_APPROVAL", "INVOICE", "INV-2026-001", "PENDING_APPROVAL", "APPROVED", "Authorized Annual AWS Cloud commitment (₹1,85,000.00)", "MEDIUM", "2026-08-16T11:30:00Z"),
            ("usr_aud_004", "Kavita Iyer", "AUDITOR", "FLAG_TRANSACTION", "INVOICE", "INV-2026-004", "SUBMITTED", "FLAGGED_FOR_REVIEW", "Flagged duplicate invoice submission pattern for SaaS licensing", "HIGH", "2026-08-17T14:45:12Z"),
            ("usr_dh_003", "Arjun Mehta", "DEPARTMENT_HEAD", "REALLOCATION_REQUEST", "BUDGET", "Engineering", "5,000,000 INR", "5,250,000 INR", "Requested GPU compute cluster expansion for AI reasoning", "MEDIUM", "2026-08-18T10:00:00Z"),
            ("usr_fm_002", "Rahul Verma", "FINANCE_MANAGER", "ALLOWANCE_OVERRIDE", "EMPLOYEE", "EMP0004", "POLICY_CAP", "AUTHORIZED_EXCEPTION", "Approved client-onsite travel expense surge during Bangalore summit", "LOW", "2026-08-19T16:20:15Z"),
            ("usr_aud_004", "Kavita Iyer", "AUDITOR", "TAX_AUDIT_VERIFIED", "FORM16", "EMP0012", "UNDER_AUDIT", "RECONCILED", "Section 80C declaration proofs verified against TDS deduction ledger", "LOW", "2026-08-20T09:10:45Z"),
            ("usr_cfo_001", "Vikramaditya Singhania", "CFO", "POLICY_CALIBRATION", "DIGITAL_TWIN", "POLICY-GOV-01", "THRESHOLD_100K", "THRESHOLD_50K", "Calibrated autonomous single-transaction approval ceiling to ₹50,000", "HIGH", "2026-08-21T13:15:00Z"),
            ("usr_fm_002", "Rahul Verma", "FINANCE_MANAGER", "RECONCILIATION_MATCH", "TRANSACTION", "TXN-2026-088", "UNMATCHED", "MATCHED", "Automated two-way ledger match with Razorpay payout gateway ref", "LOW", "2026-08-22T17:40:22Z"),
            ("usr_aud_004", "Kavita Iyer", "AUDITOR", "GST_INTEGRITY_AUDIT", "INVOICE", "INV-2026-022", "PENDING_TAX_AUDIT", "GST_VERIFIED", "18% GST calculation mathematically matched subtotal tax amount", "LOW", "2026-08-23T11:05:10Z"),
            ("usr_dh_003", "Sunita Rao", "DEPARTMENT_HEAD", "CAMPAIGN_BUDGET_SYNC", "MARKETING", "CMP-GROWTH-01", "0 INR", "50,000 INR", "Allocated autonomous growth campaign budget with 4.0x target ROAS", "LOW", "2026-08-24T14:50:00Z"),
            ("usr_fm_002", "Rahul Verma", "FINANCE_MANAGER", "VENDOR_RISK_EVALUATION", "VENDOR", "CloudNova Systems", "TIER_2", "TIER_1_PREFERRED", "Completed SOC-2 Type II vendor governance compliance review", "LOW", "2026-08-25T10:30:18Z"),
            ("usr_cfo_001", "Vikramaditya Singhania", "CFO", "LIQUIDITY_BUFFER_LOCK", "TREASURY", "TREASURY_ACCOUNT", "10,000,000 INR", "12,500,000 INR", "Locked minimum operational liquidity floor for 90-day forward runway", "HIGH", "2026-08-26T15:10:00Z"),
            ("usr_aud_004", "Kavita Iyer", "AUDITOR", "ANOMALY_ESCALATION", "INVOICE", "INV-2026-089", "REVIEW_REQUIRED", "ESCALATED_TO_CFO", "Invoice total ₹1,45,000 exceeds single-item department authorization cap", "HIGH", "2026-08-27T09:40:30Z"),
            ("usr_fm_002", "Rahul Verma", "FINANCE_MANAGER", "PAYROLL_RUN_AUTHORIZED", "PAYROLL", "PAYROLL-2026-08", "CALCULATED", "DISBURSED", "Authorized August 2026 payroll run across 100 employee records", "LOW", "2026-08-28T12:00:00Z"),
            ("usr_cfo_001", "Vikramaditya Singhania", "CFO", "SECURITY_AUDIT_PASS", "CONTROL_CENTER", "RBAC_SYSTEM", "INITIALIZED", "ACTIVE", "Completed comprehensive buildathon readiness and security scan", "LOW", "2026-08-28T18:00:00Z"),
        ]
        for user_id, user_name, role, action, entity, entity_id, old_val, new_val, details, risk, ts in initial_entries:
            payload = f"{user_id}:{action}:{entity}:{entity_id}:{ts}"
            entry_hash = self._generate_hash(payload, self._last_hash)
            entry = {
                "id": f"log_{uuid.uuid4().hex[:8]}",
                "user_id": user_id,
                "user_name": user_name,
                "role": role,
                "action": action,
                "entity": entity,
                "entity_id": entity_id,
                "old_value": old_val,
                "new_value": new_val,
                "details": details,
                "risk_level": risk,
                "timestamp": ts,
                "prev_hash": self._last_hash,
                "audit_hash": entry_hash,
            }
            self._last_hash = entry_hash
            self._logs.insert(0, entry)

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
        """Appends an immutable cryptographic audit log entry."""
        ts = datetime.now().isoformat()
        payload = f"{user_id}:{action}:{entity}:{entity_id}:{ts}:{details}"
        entry_hash = self._generate_hash(payload, self._last_hash)
        
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
            "timestamp": ts,
            "prev_hash": self._last_hash,
            "audit_hash": entry_hash,
        }
        self._last_hash = entry_hash
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
