import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Configure Windows console for Unicode output
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.app.services.budget_service import budget_service
from src.app.services.invoice_service import invoice_service
from src.app.services.anomaly_service import anomaly_service
from src.app.services.razorpay_service import razorpay_service
from src.app.tools.finance_tools import check_department_budget, audit_invoice_compliance


def test_budget_service():
    print("Testing BudgetService...")
    depts = budget_service.get_all_departments()
    assert "Engineering" in depts, "Engineering department must exist"
    assert "Marketing" in depts, "Marketing department must exist"

    eng = budget_service.get_department_budget("Engineering")
    assert eng is not None
    assert eng["allocated_budget"] > 0
    assert eng["available_balance"] > 0
    print(f"Engineering Budget Available: INR {eng['available_balance']:,.2f}")


def test_invoice_and_anomaly_service():
    print("\nTesting Invoice & Anomaly Detection Service...")
    invoices = invoice_service.get_all_invoices()
    assert len(invoices) >= 3, "Expected at least 3 initial sample invoices"

    # Test audit check with tax mismatch
    mismatched_invoice = {
        "vendor_name": "Test Vendor LLC",
        "subtotal": 10000.0,
        "tax_gst": 1800.0,
        "total_amount": 15000.0,  # Should be 11800.0
        "department": "Engineering",
    }
    res = anomaly_service.audit_invoice(mismatched_invoice)
    assert res["is_suspicious"] is True
    assert len(res["flags"]) > 0
    print(f"Flagged Anomalous Invoice: {res['flags']}")


def test_razorpay_service():
    print("\nTesting Razorpay Link Creation...")
    link_res = razorpay_service.create_payment_link(
        amount_inr=1500.0,
        description="Software License Fee",
        customer_name="John Doe",
    )
    assert link_res["success"] is True
    assert "payment_link_id" in link_res
    print(f"Generated Payment Link: {link_res['short_url']}")


def test_finance_tools():
    print("\nTesting LangChain Finance Tools...")
    tool_res = check_department_budget.invoke({"department": "Marketing"})
    assert tool_res["department"] == "Marketing"
    assert tool_res["allocated_budget"] > 0
    print("Finance tools executed successfully!")


if __name__ == "__main__":
    test_budget_service()
    test_invoice_and_anomaly_service()
    test_razorpay_service()
    test_finance_tools()
    print("\nALL AI FINANCE CONTROLLER TESTS PASSED SUCCESSFULLY!")
