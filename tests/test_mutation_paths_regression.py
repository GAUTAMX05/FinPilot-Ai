# -*- coding: utf-8 -*-
"""
============================================================================
FINPILOT AI — MUTATION PATH REGRESSION TESTS
============================================================================
Pins the fixed write paths: approving/rejecting must update budgets (not
500 midway), recon resolve accepts the UI payload shape, the allowance
alias works category-only, audits/employees tolerate null optionals.
All mutations are reverted (in-memory + JSON files) so the suite stays green.
"""

import copy
import glob
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import pytest
from fastapi.testclient import TestClient
from src.app.main import app
from src.app.core.rbac import create_access_token
from src.app.services.auth_service import auth_service
from src.app.services.budget_service import budget_service
from src.app.services.invoice_service import invoice_service
from src.app.services.employee_finance_service import employee_finance_service
from src.app.services.reconciliation_service import reconciliation_service

client = TestClient(app)
DATA_DIR = str(Path(__file__).resolve().parents[1] / "src" / "app" / "data")


def _cfo_headers() -> dict:
    user = auth_service.get_user_by_email("cfo@aifinance.local")
    token = create_access_token({"id": user["id"], "role": user["role"], "name": user["name"]})
    return {"Authorization": f"Bearer {token}"}


HEADERS = _cfo_headers()


@pytest.fixture()
def pristine_state():
    """Snapshot in-memory service state + JSON data files; restore after."""
    snap = {
        "budgets": copy.deepcopy(budget_service._data),
        "invoices": copy.deepcopy(invoice_service._invoices),
        "employees": copy.deepcopy(employee_finance_service._employees),
        "exceptions": copy.deepcopy(reconciliation_service._exceptions),
    }
    files = {}
    for f in glob.glob(os.path.join(DATA_DIR, "*.json")):
        with open(f, "r", encoding="utf-8") as fh:
            files[f] = fh.read()
    yield
    budget_service._data.clear()
    budget_service._data.update(snap["budgets"])
    invoice_service._invoices[:] = snap["invoices"]
    employee_finance_service._employees[:] = snap["employees"]
    reconciliation_service._exceptions[:] = snap["exceptions"]
    for f, content in files.items():
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(content)


def _pending_invoice():
    invs = invoice_service.get_pending_invoices("CFO", None)
    assert invs, "expected seeded pending invoices"
    return invs[0]


def test_approve_commits_budget(pristine_state):
    """Approving must flip status AND move budget (was: 500 AttributeError)."""
    inv = _pending_invoice()
    dept = inv["department"]
    amt = float(inv["total_amount"])
    before = budget_service.get_department_budget(dept)["spent_amount"]
    res = client.post("/v1/approvals/decide", headers=HEADERS,
                      json={"invoice_id": inv["invoice_id"], "approved": True,
                            "reviewer_comments": "regression"})
    assert res.status_code == 200, res.text[:200]
    assert res.json()["status"] == "approved"
    after = budget_service.get_department_budget(dept)["spent_amount"]
    assert round(after - before, 2) == round(amt, 2), f"spent {before}->{after}, amt {amt}"
    print("[PASSED] approve commits exact budget delta")


def test_reject_releases_without_spending(pristine_state):
    """Rejecting must not spend and must not crash (was: 500 AttributeError)."""
    inv = _pending_invoice()
    dept = inv["department"]
    before = budget_service.get_department_budget(dept)["spent_amount"]
    res = client.post("/v1/approvals/decide", headers=HEADERS,
                      json={"invoice_id": inv["invoice_id"], "approved": False,
                            "reviewer_comments": "regression"})
    assert res.status_code == 200, res.text[:200]
    assert res.json()["status"] == "rejected"
    after = budget_service.get_department_budget(dept)["spent_amount"]
    assert after == before, "reject must not move spent"
    print("[PASSED] reject releases reservation without spending")


def test_recon_resolve_accepts_ui_shape(pristine_state):
    """Exception Center sends {resolution_status, reviewer} (was: 422)."""
    exc = reconciliation_service.get_exceptions()[0]
    res = client.post(f"/v1/reconciliation/exceptions/{exc['exception_id']}/resolve",
                      headers=HEADERS,
                      json={"resolution_status": "MATCHED", "reviewer": "Sweep CFO"})
    assert res.status_code == 200, res.text[:200]
    res2 = client.post(f"/v1/reconciliation/exceptions/{exc['exception_id']}/resolve",
                       headers=HEADERS,
                       json={"decision": "INVESTIGATING", "comments": "sweep"})
    assert res2.status_code == 200, res2.text[:200]
    print("[PASSED] recon resolve accepts UI + canonical shapes")


def test_evaluate_allowance_alias(pristine_state):
    """Category-only alias must work (was: 404 wrong path)."""
    res = client.post("/v1/employees/EMP-0001/evaluate-allowance", headers=HEADERS,
                      json={"category": "Travel"})
    assert res.status_code == 200, res.text[:200]
    verdict = res.json()["assessment"]["verdict"]
    assert verdict in ("WITHIN_POLICY", "ABOVE_DEPARTMENT_LIMIT"), verdict
    print("[PASSED] evaluate-allowance alias returns verdict")


def test_audit_and_employee_tolerate_nulls(pristine_state):
    """Optional nulls must not 500 (was: float(None) TypeError)."""
    res = client.post("/v1/invoices/audit", headers=HEADERS,
                      json={"vendor_name": "V", "department": "Engineering",
                            "subtotal": None, "tax_gst": None, "total_amount": 5900.0})
    assert res.status_code == 200, res.text[:200]
    res = client.post("/v1/employees", headers=HEADERS,
                      json={"name": "Null Tester", "email": "null.tester@example.com",
                            "department": "Engineering", "designation": "Engineer",
                            "monthly_basic": 50000.0, "hra": None, "pf_deduction": None,
                            "monthly_allowance_limit": None})
    assert res.status_code == 200, res.text[:200]
    print("[PASSED] null optionals tolerated")


if __name__ == "__main__":
    print("run via: pytest tests/test_mutation_paths_regression.py -v")
