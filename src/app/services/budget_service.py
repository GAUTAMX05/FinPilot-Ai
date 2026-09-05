# -*- coding: utf-8 -*-
import json
import logging
import os
from typing import Dict, List, Any, Optional
from fastapi import HTTPException
from src.app.core.validators import validate_monetary_amount, validate_department, sanitize_text
from src.app.services.audit_service import audit_service

logger = logging.getLogger("BudgetService")


class BudgetService:
    """Manages department budgets, allocations, disbursements, and deterministic threshold audits."""

    def __init__(self):
        self._data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data",
            "department_budgets.json",
        )
        self._data: Dict[str, Any] = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        default_dict = {
            "fiscal_year": "2026-2027",
            "currency": "INR",
            "departments": {
                "Engineering": {"allocated_budget": 5420000.0, "spent_amount": 2050600.0, "pending_approvals": 0.0, "manager": "Rahul Sharma", "categories": {"Cloud Infrastructure": 2500000.0, "Software Subscriptions": 1000000.0}},
                "Marketing": {"allocated_budget": 2910000.0, "spent_amount": 2240000.0, "pending_approvals": 75000.0, "manager": "Priya Verma", "categories": {"Digital Ads": 1800000.0, "Events & Sponsorships": 600000.0}},
                "Sales": {"allocated_budget": 2500000.0, "spent_amount": 920000.0, "pending_approvals": 45000.0, "manager": "Aman Mehra", "categories": {"Travel & Client Entertainment": 1200000.0}},
                "Operations": {"allocated_budget": 1670000.0, "spent_amount": 750800.0, "pending_approvals": 0.0, "manager": "Aditi Verma", "categories": {"Logistics & Office Supplies": 900000.0}},
                "HR": {"allocated_budget": 1500000.0, "spent_amount": 410000.0, "pending_approvals": 15000.0, "manager": "Vikramaditya S.", "categories": {"Recruitment & Training": 800000.0}},
            }
        }
        if os.path.exists(self._data_path):
            try:
                with open(self._data_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    if isinstance(raw, dict) and "departments" in raw:
                        return raw
                    elif isinstance(raw, list):
                        dept_dict = {}
                        for d in raw:
                            dept_dict[d.get("department", "General")] = {
                                "allocated_budget": d.get("allocated_budget", 1000000.0),
                                "spent_amount": d.get("spent", 0.0),
                                "pending_approvals": d.get("committed", 0.0),
                                "manager": "Finance Lead",
                                "categories": {}
                            }
                        return {"fiscal_year": "2026-2027", "currency": "INR", "departments": dept_dict}
            except Exception as e:
                logger.error(f"Failed to load department budgets: {e}")
        return default_dict

    def _save_data(self):
        try:
            with open(self._data_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save department budgets: {e}")

    def get_all_departments(self, user_role: Optional[str] = None, user_department: Optional[str] = None) -> Dict[str, Any]:
        """Returns all department budgets. If user is Department Head, returns only their assigned department."""
        depts = self._data.get("departments", {})
        if user_role == "DEPARTMENT_HEAD" and user_department:
            return {
                k: v for k, v in depts.items()
                if k.lower() == user_department.lower()
            }
        return depts

    def get_department_budget(self, department: str, user_role: Optional[str] = None, user_department: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if user_role == "DEPARTMENT_HEAD" and user_department:
            if department.lower() != user_department.lower():
                return None
        depts = self._data.get("departments", {})
        for k, v in depts.items():
            if k.lower() == department.lower():
                res = dict(v)
                res["department"] = k
                spent = res.get("spent_amount", res.get("spent", 0.0))
                committed = res.get("pending_approvals", res.get("committed", 0.0))
                res["spent"] = spent
                res["spent_amount"] = spent
                res["committed"] = committed
                res["available_balance"] = round(res["allocated_budget"] - (spent + committed), 2)
                return res
        return None

    def modify_department_budget(
        self,
        department: str,
        new_allocated_budget: float,
        user_id: str = "USR-CFO-001",
        user_name: str = "CFO",
        role: str = "CFO",
        reason: str = "Budget adjustment",
    ) -> Dict[str, Any]:
        valid_dept = validate_department(department)
        valid_budget = validate_monetary_amount(new_allocated_budget, field_name="New Allocated Budget", min_amount=1000.0)
        clean_reason = sanitize_text(reason, field_name="Reason", max_length=500, allow_empty=False)

        depts = self._data.get("departments", {})
        target_key = None
        for k in depts.keys():
            if k.lower() == valid_dept.lower():
                target_key = k
                break

        if not target_key:
            raise HTTPException(status_code=404, detail=f"Department '{valid_dept}' not found.")

        old_budget = depts[target_key]["allocated_budget"]
        depts[target_key]["allocated_budget"] = valid_budget
        self._save_data()

        audit_service.log_action(
            user_id=user_id,
            user_name=user_name,
            role=role,
            action="BUDGET_MODIFIED",
            entity="BUDGET",
            entity_id=target_key,
            details=f"Modified budget for {target_key} from ₹{old_budget:,.2f} to ₹{valid_budget:,.2f}. Reason: {clean_reason}",
            risk_level="MEDIUM"
        )
        return depts[target_key]

    def reallocate_budget(
        self,
        from_department: str,
        to_department: str,
        amount: float,
        reason: str = "Inter-department budget reallocation",
        user_id: str = "USR-CFO-001",
        user_name: str = "Chief Financial Officer",
        role: str = "CFO"
    ) -> Dict[str, Any]:
        """
        Deterministically reallocates budget between departments.
        Enforces strict input validation, balance checking, and immutable audit logging.
        """
        valid_from = validate_department(from_department)
        valid_to = validate_department(to_department)
        valid_amount = validate_monetary_amount(amount, field_name="Reallocation Amount", min_amount=100.0)
        clean_reason = sanitize_text(reason, field_name="Reallocation Reason", max_length=500, allow_empty=False)

        if valid_from.lower() == valid_to.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Invalid reallocation: Source and destination department cannot be the same ('{valid_from}').",
            )

        depts = self._data.get("departments", {})
        src_key = None
        dst_key = None
        for k in depts.keys():
            if k.lower() == valid_from.lower():
                src_key = k
            if k.lower() == valid_to.lower():
                dst_key = k

        if not src_key:
            raise HTTPException(status_code=404, detail=f"Source department '{valid_from}' not found.")
        if not dst_key:
            raise HTTPException(status_code=404, detail=f"Destination department '{valid_to}' not found.")

        src = depts[src_key]
        dst = depts[dst_key]

        spent = src.get("spent_amount", src.get("spent", 0.0))
        committed = src.get("pending_approvals", src.get("committed", 0.0))
        available_balance = src["allocated_budget"] - (spent + committed)

        if valid_amount > available_balance:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Insufficient uncommitted budget in {src_key}. "
                    f"Requested ₹{valid_amount:,.2f}, but available uncommitted balance is ₹{available_balance:,.2f} "
                    f"(Allocated: ₹{src['allocated_budget']:,.2f}, Spent: ₹{spent:,.2f}, Committed: ₹{committed:,.2f})."
                ),
            )

        # Execute deterministic transfer
        src["allocated_budget"] = round(src["allocated_budget"] - valid_amount, 2)
        dst["allocated_budget"] = round(dst["allocated_budget"] + valid_amount, 2)
        self._save_data()

        # Record in immutable SHA-256 audit ledger
        audit_service.log_action(
            user_id=user_id,
            user_name=user_name,
            role=role,
            action="BUDGET_REALLOCATION",
            entity="BUDGET",
            entity_id=f"{src_key}->{dst_key}",
            details=f"Transferred ₹{valid_amount:,.2f} from {src_key} to {dst_key}. Reason: {clean_reason}",
            risk_level="MEDIUM"
        )

        return {
            "success": True,
            "message": f"Successfully transferred ₹{valid_amount:,.2f} from {src_key} to {dst_key}.",
            "source_department": src,
            "destination_department": dst,
            "reason": clean_reason
        }


    def record_expense(self, department: str, amount: float) -> bool:
        """Records an authorized expense against a department budget."""
        depts = self._data.get("departments", {})
        for k, v in depts.items():
            if k.lower() == department.lower():
                v["spent_amount"] = round(v.get("spent_amount", 0.0) + amount, 2)
                self._save_data()
                return True
        return False

    def _dept_entry(self, department: str):
        """Case-insensitive department lookup; returns (key, entry) or (None, None)."""
        for k, v in self._data.get("departments", {}).items():
            if k.lower() == department.lower():
                return k, v
        return None, None

    def commit_expense(self, department: str, amount: float, was_pending: bool = True) -> bool:
        """Commits an approved invoice: adds to spent and releases any
        pending reservation for it. Never lets pending_approvals go negative."""
        key, entry = self._dept_entry(department)
        if entry is None:
            return False
        entry["spent_amount"] = round(entry.get("spent_amount", 0.0) + amount, 2)
        if was_pending:
            pending_key = "pending_approvals" if "pending_approvals" in entry else (
                "committed" if "committed" in entry else None)
            if pending_key:
                entry[pending_key] = round(max(0.0, entry.get(pending_key, 0.0) - amount), 2)
        self._save_data()
        return True

    def release_reservation(self, department: str, amount: float) -> bool:
        """Releases a pending reservation (e.g. rejected invoice) without spending."""
        key, entry = self._dept_entry(department)
        if entry is None:
            return False
        pending_key = "pending_approvals" if "pending_approvals" in entry else (
            "committed" if "committed" in entry else None)
        if pending_key:
            entry[pending_key] = round(max(0.0, entry.get(pending_key, 0.0) - amount), 2)
            self._save_data()
        return True

budget_service = BudgetService()
