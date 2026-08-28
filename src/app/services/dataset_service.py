import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger("DatasetService")


class EnterpriseDatasetService:
    """
    Manages the enterprise dataset containing 500+ records:
    Departments, Budgets, Spending, Vendors, Invoices, Transactions,
    Allowances, Payroll, Form 16, and Approvals with multi-period date-span filtering.
    """

    def __init__(self):
        self._data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data",
            "enterprise_dataset.json",
        )
        self._dataset: Dict[str, Any] = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        if os.path.exists(self._data_path):
            try:
                with open(self._data_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load enterprise dataset: {e}")
        return {
            "departments": [],
            "vendors": [],
            "budgets": [],
            "spending": [],
            "employees": [],
            "allowances": [],
            "payrolls": [],
            "form16": [],
            "invoices": [],
            "transactions": [],
            "approvals": [],
            "notifications": [],
            "decisions": []
        }

    def _filter_by_date(
        self,
        records: List[Dict[str, Any]],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        date_field: str = "date"
    ) -> List[Dict[str, Any]]:
        if not start_date and not end_date:
            return records

        filtered = []
        for r in records:
            d_str = r.get(date_field)
            if not d_str:
                filtered.append(r)
                continue
            
            # Format comparison YYYY-MM-DD
            if start_date and d_str < start_date:
                continue
            if end_date and d_str > end_date:
                continue
            filtered.append(r)
        return filtered

    def get_summary(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        user_role: Optional[str] = None,
        user_department: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Returns KPI metrics and summary aggregated over the specified date span."""
        invoices = self.get_invoices(start_date, end_date, user_role, user_department)
        txns = self.get_transactions(start_date, end_date, user_role, user_department)
        
        total_inflow = sum(t["amount"] for t in txns if t.get("direction") == "Inflow" and t.get("status") == "Completed")
        total_outflow = sum(t["amount"] for t in txns if t.get("direction") == "Outflow" and t.get("status") == "Completed")
        
        invoice_total = sum(i["amount"] for i in invoices)
        paid_invoices = sum(i["amount"] for i in invoices if i.get("status") == "Paid")
        pending_invoices = sum(i["amount"] for i in invoices if i.get("status") == "Pending Review")
        approved_invoices = sum(i["amount"] for i in invoices if i.get("status") == "Approved")

        # Department spend distribution in the span
        dept_spend: Dict[str, float] = {}
        for i in invoices:
            d = i.get("department", "General")
            dept_spend[d] = dept_spend.get(d, 0.0) + i.get("amount", 0.0)

        return {
            "period": {
                "start_date": start_date or "2026-04-01",
                "end_date": end_date or "2026-08-31",
                "label": f"{start_date or '2026-04-01'} to {end_date or '2026-08-31'}"
            },
            "metrics": {
                "total_inflow": round(total_inflow, 2),
                "total_outflow": round(total_outflow, 2),
                "net_cash_flow": round(total_inflow - total_outflow, 2),
                "total_invoice_volume": round(invoice_total, 2),
                "paid_invoices_amount": round(paid_invoices, 2),
                "pending_invoices_amount": round(pending_invoices, 2),
                "approved_invoices_amount": round(approved_invoices, 2),
                "invoice_count": len(invoices),
                "transaction_count": len(txns),
                "employee_count": len(self._dataset.get("employees", [])),
            },
            "department_spend": dept_spend,
        }

    def get_invoices(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        user_role: Optional[str] = None,
        user_department: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        all_inv = self._dataset.get("invoices", [])
        if user_role == "DEPARTMENT_HEAD" and user_department:
            all_inv = [i for i in all_inv if i.get("department", "").lower() == user_department.lower()]
        if status:
            all_inv = [i for i in all_inv if i.get("status", "").lower() == status.lower()]
        return self._filter_by_date(all_inv, start_date, end_date, date_field="date")

    def get_transactions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        user_role: Optional[str] = None,
        user_department: Optional[str] = None,
        direction: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        all_txns = self._dataset.get("transactions", [])
        if user_role == "DEPARTMENT_HEAD" and user_department:
            all_txns = [t for t in all_txns if t.get("department", "").lower() == user_department.lower()]
        if direction:
            all_txns = [t for t in all_txns if t.get("direction", "").lower() == direction.lower()]
        if status:
            all_txns = [t for t in all_txns if t.get("status", "").lower() == status.lower()]
        return self._filter_by_date(all_txns, start_date, end_date, date_field="date")

    def get_employees(
        self,
        user_role: Optional[str] = None,
        user_department: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        emps = self._dataset.get("employees", [])
        if user_role == "DEPARTMENT_HEAD" and user_department:
            return [e for e in emps if e.get("department", "").lower() == user_department.lower()]
        return emps

    def get_allowances(
        self,
        user_role: Optional[str] = None,
        user_department: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        allow = self._dataset.get("allowances", [])
        if user_role == "DEPARTMENT_HEAD" and user_department:
            return [a for a in allow if a.get("department", "").lower() == user_department.lower()]
        return allow

    def get_payroll(
        self,
        user_role: Optional[str] = None,
        user_department: Optional[str] = None,
        period: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        pay = self._dataset.get("payrolls", [])
        if user_role == "DEPARTMENT_HEAD" and user_department:
            pay = [p for p in pay if p.get("department", "").lower() == user_department.lower()]
        if period:
            pay = [p for p in pay if p.get("period") == period]
        return pay

    def get_form16(
        self,
        user_role: Optional[str] = None,
        user_department: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        f16 = self._dataset.get("form16", [])
        if user_role == "DEPARTMENT_HEAD" and user_department:
            return [f for f in f16 if f.get("department", "").lower() == user_department.lower()]
        return f16

    def get_spending_trends(
        self,
        user_role: Optional[str] = None,
        user_department: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        sp = self._dataset.get("spending", [])
        if user_role == "DEPARTMENT_HEAD" and user_department:
            return [s for s in sp if s.get("department", "").lower() == user_department.lower()]
        return sp


dataset_service = EnterpriseDatasetService()
