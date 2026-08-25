import os
import json
import uuid
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("InvoiceService")


class InvoiceService:
    """Manages invoice repository, parsing, status updates, and compliance with RBAC filtering."""

    def __init__(self):
        self._data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data",
            "sample_invoices.json",
        )
        self._invoices: List[Dict[str, Any]] = self._load_invoices()

    def _load_invoices(self) -> List[Dict[str, Any]]:
        if os.path.exists(self._data_path):
            try:
                with open(self._data_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load invoices: {e}")
        return []

    def _save_invoices(self):
        try:
            with open(self._data_path, "w", encoding="utf-8") as f:
                json.dump(self._invoices, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save invoices: {e}")

    def get_all_invoices(
        self,
        user_role: Optional[str] = None,
        user_department: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Returns invoices filtered by role/department permissions."""
        if user_role == "DEPARTMENT_HEAD" and user_department:
            return [
                inv for inv in self._invoices
                if inv.get("department", "").lower() == user_department.lower()
            ]
        return self._invoices

    def get_invoice_by_id(
        self,
        invoice_id: str,
        user_role: Optional[str] = None,
        user_department: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        for inv in self._invoices:
            if inv.get("invoice_id") == invoice_id:
                if user_role == "DEPARTMENT_HEAD" and user_department:
                    if inv.get("department", "").lower() != user_department.lower():
                        return None  # Scoped isolation
                return inv
        return None

    def add_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        if "invoice_id" not in invoice_data:
            invoice_data["invoice_id"] = f"INV-2026-{uuid.uuid4().hex[:4].upper()}"
        self._invoices.append(invoice_data)
        self._save_invoices()
        return invoice_data

    def update_invoice_status(
        self,
        invoice_id: str,
        new_status: str,
        decided_by_id: Optional[str] = None,
        decided_by_name: Optional[str] = None,
        comments: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        for inv in self._invoices:
            if inv.get("invoice_id") == invoice_id:
                inv["status"] = new_status
                if decided_by_id:
                    inv["decided_by_id"] = decided_by_id
                    inv["decided_by_name"] = decided_by_name
                    inv["decision_comments"] = comments
                self._save_invoices()
                return inv
        return None

    def get_pending_invoices(
        self,
        user_role: Optional[str] = None,
        user_department: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        pending = [inv for inv in self._invoices if inv.get("status") == "pending_approval"]
        if user_role == "DEPARTMENT_HEAD" and user_department:
            return [
                inv for inv in pending
                if inv.get("department", "").lower() == user_department.lower()
            ]
        return pending


invoice_service = InvoiceService()
