import logging
from typing import Dict, Any, List
from src.app.services.budget_service import budget_service
from src.app.services.invoice_service import invoice_service
from src.app.core.config import settings

logger = logging.getLogger("AnomalyService")


class AnomalyService:
    """Detects duplicate billings, tax math inaccuracies, budget overruns, and policy breaches."""

    def audit_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        flags: List[str] = []
        is_suspicious = False
        requires_hitl = False

        vendor = invoice_data.get("vendor_name", "Unknown Vendor")
        subtotal = float(invoice_data.get("subtotal", 0.0))
        tax = float(invoice_data.get("tax_gst", 0.0))
        total = float(invoice_data.get("total_amount", subtotal + tax))
        department = invoice_data.get("department", "Operations")

        # 1. Tax calculation consistency check (GST in India is typically 18% standard, or 5%/12%/28%)
        expected_total = round(subtotal + tax, 2)
        if abs(total - expected_total) > 1.0:
            flags.append(f"Tax / Subtotal mismatch: Total ({total}) does not equal Subtotal ({subtotal}) + Tax ({tax}).")
            is_suspicious = True

        # 2. Check for duplicate invoice (same vendor and exact amount within existing records)
        existing_invoices = invoice_service.get_all_invoices()
        current_id = invoice_data.get("invoice_id")
        for ex in existing_invoices:
            if ex.get("invoice_id") != current_id:
                if ex.get("vendor_name", "").lower() == vendor.lower() and abs(ex.get("total_amount", 0) - total) < 0.01:
                    flags.append(f"Potential Duplicate: Invoice matches previous invoice {ex.get('invoice_id')} for {vendor} with exact amount ₹{total}.")
                    is_suspicious = True

        # 3. Department Budget Capacity Check
        dept_info = budget_service.get_department_budget(department)
        if dept_info:
            avail = dept_info.get("available_balance", 0.0)
            if total > avail:
                flags.append(f"Budget Overrun Risk: Requested ₹{total:,.2f} exceeds {department}'s remaining budget of ₹{avail:,.2f}.")
                is_suspicious = True

        # 4. Check HITL Governance Threshold
        if total >= settings.HITL_APPROVAL_THRESHOLD_INR:
            flags.append(f"HITL Required: Amount ₹{total:,.2f} exceeds autonomous threshold of ₹{settings.HITL_APPROVAL_THRESHOLD_INR:,.2f}.")
            requires_hitl = True

        status = "FLAGGED" if is_suspicious else ("NEEDS_APPROVAL" if requires_hitl else "CLEARED")

        return {
            "is_suspicious": is_suspicious,
            "requires_hitl": requires_hitl,
            "status": status,
            "flags": flags,
            "confidence_score": 0.95 if not is_suspicious else 0.40,
        }


anomaly_service = AnomalyService()
