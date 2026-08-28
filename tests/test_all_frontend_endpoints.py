import sys
import json
import urllib.request
import urllib.error

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(name, path, method="GET", body=None, headers=None):
    headers = headers or {}
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    if body and "Content-Type" not in headers:
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            content = resp.read().decode("utf-8")
            try:
                parsed = json.loads(content)
                print(f"[PASS] {method} {path} -> {status}")
                return True, parsed
            except Exception:
                print(f"[PASS] {method} {path} -> {status}")
                return True, content
    except urllib.error.HTTPError as e:
        err_content = e.read().decode("utf-8")
        print(f"[FAIL] {method} {path} -> HTTP {e.code}: {err_content[:200]}")
        return False, err_content
    except Exception as e:
        print(f"[ERROR] {method} {path} -> {e}")
        return False, str(e)

def run_frontend_api_tests():
    print("==================================================================")
    print("  FINPILOT AI — TEST ALL 44 FRONTEND API CALLS                   ")
    print("==================================================================")

    endpoints = [
        # Digital Twin & What-If
        ("Digital Twin State", "/v1/simulation/digital-twin-state", "GET", None),
        ("Policy Calibrations", "/v1/simulation/policy-calibrations", "GET", None),
        ("What-If Simulation", "/v1/simulation/what-if", "POST", {"scenario": "Can we afford ₹500,000 for Engineering?"}),
        ("Causal Analysis", "/v1/simulation/causal-analysis?anomaly_query=Engineering", "GET", None),
        ("Apply Policy Calibration", "/v1/simulation/apply-policy-calibration", "POST", {"proposal_id": "PROP-CALIB-001"}),

        # Notifications
        ("Get Notifications", "/v1/notifications?category=ALL", "GET", None),
        ("Resolve Notification", "/v1/notifications/NOTIF-2026-001/resolve", "POST", {"resolution_note": "Resolved in test"}),
        ("Notify Finance Team", "/v1/notifications/NOTIF-2026-002/notify-finance", "POST", {}),
        ("Mark All Read", "/v1/notifications/mark-all-read", "POST", {}),
        ("Clear Notifications", "/v1/notifications/clear", "POST", {}),

        # Intelligence & Charts
        ("Analytics Series", "/v1/intelligence/analytics-series?metric=burn&period=daily", "GET", None),
        ("Watchtower Radar", "/v1/intelligence/watchtower", "GET", None),
        ("Decision Tree Eval", "/v1/intelligence/decision-tree-eval?event_id=EXP-2026-8801", "GET", None),
        ("Company Decision Map", "/v1/intelligence/company-decision-map", "GET", None),
        ("Budget Forecasts", "/v1/intelligence/forecasts", "GET", None),
        ("Vendors Intelligence", "/v1/intelligence/vendors", "GET", None),
        ("Affordability Analysis", "/v1/intelligence/affordability", "POST", {
            "department": "Engineering",
            "amount": 500000.0,
            "category": "Cloud Infrastructure",
            "description": "Cloud cluster expansion"
        }),
        ("Executive Report", "/v1/intelligence/report", "GET", None),

        # Budgets & Invoices
        ("Department Budgets", "/v1/budgets", "GET", None),
        ("Budget Reallocate", "/v1/budgets/reallocate", "POST", {
            "from_department": "Operations",
            "to_department": "Engineering",
            "amount": 10000.0,
            "reason": "Test rebalance"
        }),
        ("Invoices List", "/v1/invoices", "GET", None),
        ("Create Invoice", "/v1/invoices", "POST", {
            "invoice_number": "INV-TEST-999",
            "vendor_name": "Test Vendor",
            "department": "Engineering",
            "category": "Cloud Infrastructure",
            "amount": 25000.0,
            "gst_rate": 0.18,
            "items": [{"description": "Cloud storage", "amount": 25000.0}]
        }),

        # Approvals & Reconciliation
        ("Approvals Pending", "/v1/approvals/pending", "GET", None),
        ("Approvals Decide", "/v1/approvals/decide", "POST", {
            "invoice_id": "INV-2026-001",
            "decision": "APPROVED",
            "notes": "Approved in test"
        }),
        ("Reconciliation Exceptions", "/v1/reconciliation/exceptions", "GET", None),
        ("Reconciliation Run", "/v1/reconciliation/run", "POST", {}),
        ("Cash Flow Forecast", "/v1/cash-flow/forecast", "GET", None),

        # People & Tax
        ("Tax Reconciliation", "/v1/payroll/tax-reconciliation", "GET", None),
        ("Tax Resolve", "/v1/payroll/tax-reconciliation/EMP-1042/resolve", "POST", {"resolution_note": "Tax mismatch verified"}),
        ("Tax Notify Finance", "/v1/payroll/tax-reconciliation/EMP-1042/notify-finance", "POST", {}),
        ("Employees List", "/v1/employees", "GET", None),
        ("Allowance Anomalies", "/v1/employees/anomalies/allowance", "GET", None),
        ("Get Employee EMP-101", "/v1/employees/EMP-101", "GET", None),
        ("Revise Salary", "/v1/employees/EMP-101/revise-salary", "POST", {"new_monthly_salary": 85000.0, "effective_date": "2026-09-01"}),
        ("Deactivate Employee", "/v1/employees/EMP-101/deactivate", "POST", {"reason": "Test deactivation"}),

        # Governance & Audit
        ("Audit Logs", "/v1/audit/logs", "GET", None),

        # Agent Chat Copilot
        ("Agent Chat", "/v1/agent/chat", "POST", {
            "message": "Are we overspending? Analyze all department run-rates vs time elapsed in fiscal year."
        }),

        # Commerce & Growth Studio
        ("AI Manifest", "/v1/commerce/ai-manifest", "GET", None),
        ("Commerce Catalog", "/v1/commerce/catalog", "GET", None),
        ("Conversational Checkout", "/v1/commerce/conversational-checkout", "POST", {
            "message": "I want to buy Ultra API Gateway",
            "cart": []
        }),
        ("AI-to-AI Buy", "/v1/commerce/ai-buy", "POST", {
            "buyer_agent_id": "TEST-BOT",
            "spending_token_limit_inr": 100000.0,
            "items": [{"product_id": "PROD-API-01", "quantity": 1}],
            "negotiation_requested": True
        }),
        ("Growth Campaigns", "/v1/commerce/campaigns", "GET", None),
        ("Growth Campaign Create", "/v1/commerce/campaigns/create", "POST", {
            "name": "Test Campaign",
            "target_audience": "Tech Startups",
            "discount_pct": 10.0,
            "allocated_marketing_budget": 5000.0,
            "product_ids": ["PROD-API-01"]
        }),
        ("Simulate Failure: Timeout", "/v1/commerce/simulate-failure", "POST", {"failure_type": "API_GATEWAY_TIMEOUT"}),
        ("Simulate Failure: Payload", "/v1/commerce/simulate-failure", "POST", {"failure_type": "INVALID_PAYLOAD"}),
        ("Simulate Failure: Budget", "/v1/commerce/simulate-failure", "POST", {"failure_type": "BUDGET_CAP_BREACH"}),
        ("Simulate Failure: Token", "/v1/commerce/simulate-failure", "POST", {"failure_type": "TOKEN_SPENDING_OVERAGE"}),
    ]

    passed = 0
    failed = 0
    for name, path, method, body in endpoints:
        ok, res = test_endpoint(name, path, method, body)
        if ok:
            passed += 1
        else:
            failed += 1

    print("\n==================================================================")
    print(f"FRONTEND API TEST SUMMARY: {passed} PASSED, {failed} FAILED (Total: {len(endpoints)})")
    print("==================================================================")

if __name__ == "__main__":
    run_frontend_api_tests()
