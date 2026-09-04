# -*- coding: utf-8 -*-
"""
============================================================================
FINPILOT AI — DATA-BACKED ENDPOINTS SMOKE TEST
============================================================================
Guards against the "empty widget" regression class: dashboard cards/tables
that render their shell but no data (e.g. the "Key Outflow & Liquidity
Drivers" card, which stayed empty because the backend never emitted the
`forecast.recurring_drivers` list the frontend reads).

Hits every major data-backed GET endpoint against the seeded demo dataset
and asserts each returns at least one non-empty record (plus the exact
contract fields the UI renders). Fails CI instead of silently shipping an
empty-data demo.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from fastapi.testclient import TestClient
from src.app.main import app
from src.app.core.rbac import create_access_token
from src.app.services.auth_service import auth_service

client = TestClient(app)

SPAN = "start_date=2026-01-01&end_date=2026-12-31"


def _cfo_headers() -> dict:
    user = auth_service.get_user_by_email("cfo@aifinance.local")
    token = create_access_token({"id": user["id"], "role": user["role"], "name": user["name"]})
    return {"Authorization": f"Bearer {token}"}


HEADERS = _cfo_headers()


def _get(path: str) -> dict:
    res = client.get(path, headers=HEADERS)
    assert res.status_code == 200, f"GET {path} -> HTTP {res.status_code}: {res.text[:200]}"
    body = res.json()
    assert body.get("success", True) is True, f"GET {path} success!=True: {str(body)[:200]}"
    return body


def _assert_nonempty_list(body: dict, key: str, path: str, min_count: int = 1):
    items = body.get(key)
    assert isinstance(items, list), f"GET {path}: '{key}' is not a list: {type(items).__name__}"
    assert len(items) >= min_count, f"GET {path}: '{key}' empty (expected>={min_count})"
    return items


def test_cash_flow_forecast_has_horizons_and_drivers():
    """Regression: drivers card was empty (backend sent key_drivers strings only)."""
    body = _get("/v1/cash-flow/forecast")
    fc = body["forecast"]
    for h in ("seven_day", "thirty_day", "ninety_day", "fiscal_year"):
        assert h in fc["horizons"], f"missing horizon {h}"
        assert isinstance(fc["horizons"][h]["projected_liquidity"], (int, float))
    drivers = _assert_nonempty_list(fc, "recurring_drivers", "/v1/cash-flow/forecast", 3)
    for d in drivers:
        for field in ("name", "frequency", "department", "amount"):
            assert field in d, f"driver missing '{field}': {d}"
        assert isinstance(d["amount"], (int, float)), f"driver amount not numeric: {d}"
    assert len(fc.get("daily_curve", [])) >= 10
    print("[PASSED] cash-flow forecast incl. recurring_drivers")


def test_dataset_tables_nonempty():
    inv = _get(f"/v1/dataset/invoices?{SPAN}")
    invs = _assert_nonempty_list(inv, "invoices", "dataset/invoices", 100)
    assert {"invoice_id", "vendor_name", "total_amount", "status"} <= set(invs[0].keys())

    txn = _get(f"/v1/dataset/transactions?{SPAN}")
    txns = _assert_nonempty_list(txn, "transactions", "dataset/transactions", 100)
    assert {"transaction_id", "date", "department", "direction", "amount", "status"} <= set(txns[0].keys())

    emp = _get(f"/v1/dataset/employees?{SPAN}")
    _assert_nonempty_list(emp, "employees", "dataset/employees", 50)

    allow = _get(f"/v1/dataset/allowances?{SPAN}")
    _assert_nonempty_list(allow, "allowances", "dataset/allowances")

    f16 = _get(f"/v1/dataset/form16?{SPAN}")
    _assert_nonempty_list(f16, "form16", "dataset/form16")

    pay = _get("/v1/dataset/payroll?period=2026-08")
    _assert_nonempty_list(pay, "payroll", "dataset/payroll")

    summ = _get(f"/v1/dataset/summary?{SPAN}")
    assert summ["data"]["metrics"], "summary metrics empty"
    print("[PASSED] dataset tables (invoices/txns/employees/allowances/form16/payroll/summary)")


def test_finance_tables_nonempty():
    inv2 = _get("/v1/invoices")
    _assert_nonempty_list(inv2, "invoices", "/v1/invoices", 100)

    emp2 = _get("/v1/employees")
    _assert_nonempty_list(emp2, "employees", "/v1/employees", 50)

    bud = _get("/v1/budgets")
    assert len(bud.get("departments", {})) >= 5, "expected >=5 departments"

    appr = _get("/v1/approvals/pending")
    assert isinstance(appr.get("pending_invoices"), list)

    audit = _get("/v1/audit/logs")
    _assert_nonempty_list(audit, "logs", "/v1/audit/logs")

    ano = _get("/v1/employees/anomalies/allowance")
    _assert_nonempty_list(ano, "anomalies", "allowance anomalies")
    print("[PASSED] finance tables (invoices/employees/budgets/approvals/audit/anomalies)")


def test_controller_and_simulation_nonempty():
    dash = _get("/v1/controller/dashboard")
    assert dash.get("run_summary"), "dashboard run_summary empty"
    assert isinstance(dash.get("exceptions"), list) and dash["exceptions"], "dashboard exceptions empty"
    assert dash.get("evaluation"), "dashboard evaluation empty"
    assert dash.get("gateway_status"), "dashboard gateway_status empty"

    exc = _get("/v1/reconciliation/exceptions")
    _assert_nonempty_list(exc, "exceptions", "reconciliation/exceptions")

    twin = _get("/v1/simulation/digital-twin-state")
    assert twin["state"]["cash_position"]["liquid_reserves"] > 0
    assert len(twin["baseline_90d_trajectory"]["cash_trajectory"]) >= 5

    cal = _get("/v1/simulation/policy-calibrations")
    _assert_nonempty_list(cal, "proposals", "policy-calibrations")

    causal = _get("/v1/simulation/causal-analysis?anomaly_query=Engineering%20budget%20overrun")
    assert causal["causal_analysis"]["primary_cause"], "causal primary_cause empty"
    print("[PASSED] controller + simulation widgets")


def test_intelligence_commerce_notifications_nonempty():
    fc = _get("/v1/intelligence/forecasts")
    _assert_nonempty_list(fc, "forecasts", "forecasts", 5)

    ven = _get("/v1/intelligence/vendors")
    vendors = _assert_nonempty_list(ven, "vendors", "vendors")
    assert {"vendor_name", "total_spend", "risk_score", "status"} <= set(vendors[0].keys())

    wt = _get("/v1/intelligence/watchtower")
    _assert_nonempty_list(wt, "alerts", "watchtower")

    hs = _get("/v1/intelligence/health-score")
    assert hs["data"]["overall_score"] > 0

    dm = _get("/v1/intelligence/company-decision-map")
    assert dm["decision_map"], "decision map empty"

    cat = _get("/v1/commerce/catalog")
    _assert_nonempty_list(cat, "products", "catalog")

    camp = _get("/v1/commerce/campaigns")
    assert isinstance(camp.get("campaigns"), list)

    notif = _get("/v1/notifications")
    _assert_nonempty_list(notif, "notifications", "notifications")

    d = _get("/v1/notifications/directory")
    _assert_nonempty_list(d, "directory", "directory")
    print("[PASSED] intelligence + commerce + notifications")


if __name__ == "__main__":
    test_cash_flow_forecast_has_horizons_and_drivers()
    test_dataset_tables_nonempty()
    test_finance_tables_nonempty()
    test_controller_and_simulation_nonempty()
    test_intelligence_commerce_notifications_nonempty()
    print("ALL DATA-BACKED ENDPOINT SMOKE TESTS PASSED")
