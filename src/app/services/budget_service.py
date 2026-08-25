import os
import json
import logging
from typing import Dict, Any, Optional
from src.app.services.audit_service import audit_service

logger = logging.getLogger("BudgetService")


class BudgetService:
    """Manages department budget allocations, burn tracking, and runway health with RBAC filtering."""

    def __init__(self):
        self._data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data",
            "department_budgets.json",
        )
        self._budgets: Dict[str, Any] = self._load_budgets()

    def _load_budgets(self) -> Dict[str, Any]:
        if os.path.exists(self._data_path):
            try:
                with open(self._data_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load budget data from {self._data_path}: {e}")
        return {"fiscal_year": "2026-2027", "currency": "INR", "departments": {}}

    def _save_budgets(self):
        try:
            with open(self._data_path, "w", encoding="utf-8") as f:
                json.dump(self._budgets, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save budget data: {e}")

    def get_all_departments(
        self,
        user_role: Optional[str] = None,
        user_department: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Returns all department budgets or filtered for Department Head."""
        all_depts = self._budgets.get("departments", {})

        # If role is DEPARTMENT_HEAD, enforce department-level data security
        if user_role == "DEPARTMENT_HEAD" and user_department:
            filtered = {}
            for name, data in all_depts.items():
                if name.lower() == user_department.lower():
                    filtered[name] = data
            return filtered

        return all_depts

    def get_department_budget(
        self,
        department: str,
        user_role: Optional[str] = None,
        user_department: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        # Enforce security for Department Head
        if user_role == "DEPARTMENT_HEAD" and user_department:
            if department.strip().lower() != user_department.strip().lower():
                return None  # Unauthorized

        depts = self._budgets.get("departments", {})
        for dept_name, info in depts.items():
            if dept_name.lower() == department.strip().lower():
                allocated = info.get("allocated_budget", 0.0)
                spent = info.get("spent_amount", 0.0)
                pending = info.get("pending_approvals", 0.0)
                remaining = allocated - spent - pending
                utilization_pct = round((spent / allocated) * 100, 2) if allocated > 0 else 0.0
                return {
                    "department": dept_name,
                    "manager": info.get("manager"),
                    "allocated_budget": allocated,
                    "spent_amount": spent,
                    "pending_approvals": pending,
                    "available_balance": remaining,
                    "utilization_percentage": utilization_pct,
                    "categories": info.get("categories", {}),
                }
        return None

    def modify_department_budget(
        self,
        department: str,
        new_allocated_budget: float,
        user_id: str,
        user_name: str,
        role: str,
        reason: str = "",
    ) -> Dict[str, Any]:
        """Modifies allocated budget for a department (CFO or Finance Manager)."""
        depts = self._budgets.get("departments", {})
        for dept_name, info in depts.items():
            if dept_name.lower() == department.strip().lower():
                old_val = f"{info.get('allocated_budget', 0.0):,.2f} INR"
                info["allocated_budget"] = float(new_allocated_budget)
                self._save_budgets()

                audit_service.log_action(
                    user_id=user_id,
                    user_name=user_name,
                    role=role,
                    action="MODIFY_BUDGET",
                    entity="DEPARTMENT_BUDGET",
                    entity_id=dept_name,
                    old_value=old_val,
                    new_value=f"{float(new_allocated_budget):,.2f} INR",
                    details=f"Budget modified: {reason}",
                    risk_level="MEDIUM",
                )
                return {"success": True, "department": dept_name, "new_allocated": new_allocated_budget}
        raise ValueError(f"Department '{department}' not found.")

    def reallocate_budget(
        self,
        from_department: str,
        to_department: str,
        amount: float,
        user_id: str,
        user_name: str,
        role: str,
        reason: str = "",
    ) -> Dict[str, Any]:
        """Reallocates budget from one department to another (CFO exclusive)."""
        depts = self._budgets.get("departments", {})
        from_info = None
        to_info = None
        for dept_name, info in depts.items():
            if dept_name.lower() == from_department.strip().lower():
                from_info = (dept_name, info)
            if dept_name.lower() == to_department.strip().lower():
                to_info = (dept_name, info)

        if not from_info or not to_info:
            raise ValueError("Source or destination department not found.")

        from_name, from_data = from_info
        to_name, to_data = to_info

        if from_data["allocated_budget"] < amount:
            raise ValueError(f"Insufficient funds in {from_name} to reallocate ₹{amount:,.2f}.")

        from_data["allocated_budget"] -= amount
        to_data["allocated_budget"] += amount
        self._save_budgets()

        audit_service.log_action(
            user_id=user_id,
            user_name=user_name,
            role=role,
            action="REALLOCATE_BUDGET",
            entity="DEPARTMENT_BUDGET",
            entity_id=f"{from_name}->{to_name}",
            old_value=f"{from_name}: ₹{from_data['allocated_budget']+amount:,.2f}",
            new_value=f"{from_name}: ₹{from_data['allocated_budget']:,.2f}, {to_name}: ₹{to_data['allocated_budget']:,.2f}",
            details=f"Reallocated ₹{amount:,.2f} from {from_name} to {to_name}. Reason: {reason}",
            risk_level="HIGH",
        )
        return {"success": True, "reallocated_amount": amount, "from": from_name, "to": to_name}

    def reserve_budget(self, department: str, amount: float) -> bool:
        """Reserves amount into pending_approvals until approved."""
        depts = self._budgets.get("departments", {})
        for dept_name, info in depts.items():
            if dept_name.lower() == department.strip().lower():
                info["pending_approvals"] = info.get("pending_approvals", 0.0) + amount
                self._save_budgets()
                return True
        return False

    def commit_expense(self, department: str, amount: float, was_pending: bool = True) -> bool:
        """Moves expense to spent_amount."""
        depts = self._budgets.get("departments", {})
        for dept_name, info in depts.items():
            if dept_name.lower() == department.strip().lower():
                if was_pending:
                    info["pending_approvals"] = max(0.0, info.get("pending_approvals", 0.0) - amount)
                info["spent_amount"] = info.get("spent_amount", 0.0) + amount
                self._save_budgets()
                return True
        return False

    def release_reservation(self, department: str, amount: float) -> bool:
        """Releases pending reservation upon rejection."""
        depts = self._budgets.get("departments", {})
        for dept_name, info in depts.items():
            if dept_name.lower() == department.strip().lower():
                info["pending_approvals"] = max(0.0, info.get("pending_approvals", 0.0) - amount)
                self._save_budgets()
                return True
        return False


budget_service = BudgetService()
