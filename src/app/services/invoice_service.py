# -*- coding: utf-8 -*-
import os
import json
import uuid
import logging
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from src.app.core.validators import validate_monetary_amount, validate_department, sanitize_text
from src.app.services.audit_service import audit_service

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
        clean_id = sanitize_text(invoice_id, field_name="Invoice ID", max_length=50, allow_empty=False)
        for inv in self._invoices:
            if inv.get("invoice_id") == clean_id:
                if user_role == "DEPARTMENT_HEAD" and user_department:
                    if inv.get("department", "").lower() != user_department.lower():
                        return None  # Scoped isolation
                return inv
        return None

    def add_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validates and adds an invoice record to the ledger."""
        raw_amt = invoice_data.get("total_amount") or invoice_data.get("amount")
        valid_amount = validate_monetary_amount(raw_amt, field_name="Invoice Total Amount", min_amount=1.0)
        valid_dept = validate_department(invoice_data.get("department", "General"))
        clean_vendor = sanitize_text(invoice_data.get("vendor_name"), field_name="Vendor Name", max_length=100, allow_empty=False)
        clean_cat = sanitize_text(invoice_data.get("category", "General"), field_name="Category", max_length=50)

        invoice_id = invoice_data.get("invoice_id") or f"INV-2026-{uuid.uuid4().hex[:4].upper()}"
        clean_inv_id = sanitize_text(invoice_id, field_name="Invoice ID", max_length=50)

        record = {
            "invoice_id": clean_inv_id,
            "department": valid_dept,
            "date": invoice_data.get("date", "2026-08-15"),
            "status": invoice_data.get("status", "Pending Review"),
            "amount": valid_amount,
            "total_amount": valid_amount,
            "vendor_name": clean_vendor,
            "vendor_id": invoice_data.get("vendor_id", f"VEN-{uuid.uuid4().hex[:4].upper()}"),
            "purchase_order": invoice_data.get("purchase_order", f"PO-{uuid.uuid4().hex[:4].upper()}"),
            "category": clean_cat,
            "gst_rate": 18.0,
            "gst_amount": round(valid_amount * 0.18 / 1.18, 2),
            "subtotal": round(valid_amount / 1.18, 2)
        }

        self._invoices.append(record)
        self._save_invoices()
        return record

    def update_invoice_status(
        self,
        invoice_id: str,
        new_status: str,
        decided_by_id: Optional[str] = None,
        decided_by_name: Optional[str] = None,
        comments: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        clean_id = sanitize_text(invoice_id, field_name="Invoice ID", max_length=50, allow_empty=False)
        clean_comments = sanitize_text(comments, field_name="Comments", max_length=500) if comments else None

        for inv in self._invoices:
            if inv.get("invoice_id") == clean_id:
                inv["status"] = new_status
                if decided_by_id:
                    inv["decided_by_id"] = decided_by_id
                    inv["decided_by_name"] = decided_by_name
                    inv["decision_comments"] = clean_comments
                self._save_invoices()
                return inv
        return None

    def get_pending_invoices(
        self,
        user_role: Optional[str] = None,
        user_department: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        pending = [inv for inv in self._invoices if inv.get("status") in ["Pending Review", "pending_approval"]]
        if user_role == "DEPARTMENT_HEAD" and user_department:
            return [
                inv for inv in pending
                if inv.get("department", "").lower() == user_department.lower()
            ]
        return pending


invoice_service = InvoiceService()
