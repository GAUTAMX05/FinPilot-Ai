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
        with urllib.request.urlopen(req, timeout=8) as resp:
            status = resp.status
            content = resp.read().decode("utf-8")
            try:
                parsed = json.loads(content)
                print(f"[PASS] {method} {path} -> {status} (JSON valid)")
                return True, parsed
            except Exception:
                print(f"[PASS] {method} {path} -> {status} (Non-JSON or raw HTML)")
                return True, content
    except urllib.error.HTTPError as e:
        err_content = e.read().decode("utf-8")
        print(f"[FAIL] {method} {path} -> HTTP {e.code}: {err_content[:200]}")
        return False, err_content
    except Exception as e:
        print(f"[ERROR] {method} {path} -> {e}")
        return False, str(e)

def run_diagnostics():
    print("==================================================================")
    print("       FINPILOT AI — SYSTEM-WIDE ENDPOINT DIAGNOSTICS            ")
    print("==================================================================")

    endpoints = [
        # System & Core
        ("Health Check", "/health", "GET", None),
        ("Static UI", "/", "GET", None),

        # Auth & Users
        ("Users List", "/v1/users", "GET", None),

        # Decision Control & Digital Twin
        ("Digital Twin Snapshot", "/v1/simulation/digital-twin-state", "GET", None),
        ("Policy Calibrations", "/v1/simulation/policy-calibrations", "GET", None),
        ("Digital Twin Forward Sim", "/v1/simulation/forward-simulation", "POST", {
            "days": 90,
            "spend_velocity_multiplier": 1.1,
            "vendor_delay_days": 10,
            "headcount_addition": 2
        }),
        ("Action Affordability Sim", "/v1/simulation/simulate-action", "POST", {
            "action_type": "EXPENSE",
            "department": "Engineering",
            "amount": 500000.0,
            "description": "Cloud cluster upgrade"
        }),
        ("Decision Map Data", "/v1/intelligence/decision-map", "GET", None),
        ("Decision Tree Check", "/v1/intelligence/decision-tree/check", "POST", {
            "invoice_id": "INV-2026-001",
            "amount": 100300.0,
            "department": "Engineering",
            "vendor": "CloudOps"
        }),
        ("Analytics Timeseries", "/v1/intelligence/analytics/timeseries?metric=burn&period=daily", "GET", None),
        ("Watchtower Radar", "/v1/intelligence/watchtower", "GET", None),

        # AI Chat & Copilot
        ("AI Chat Pipeline", "/v1/chat", "POST", {
            "message": "Can we afford another ₹500,000 cloud infrastructure expense for Engineering?",
            "thread_id": "test-diag-thread"
        }),

        # Financial Operations
        ("Department Budgets", "/v1/budgets", "GET", None),
        ("Invoices List", "/v1/invoices", "GET", None),
        ("Approvals Queue", "/v1/approvals", "GET", None),
        ("Reconciliation", "/v1/reconciliation/status", "GET", None),
        ("Cash Flow Forecast", "/v1/cash-flow/forecast", "GET", None),
        ("Vendors Radar", "/v1/intelligence/vendors/risk", "GET", None),

        # People & Tax
        ("Employees Master", "/v1/employees", "GET", None),
        ("Tax Reconciliation", "/v1/payroll/tax-reconciliation", "GET", None),
        ("Notifications", "/v1/notifications", "GET", None),

        # Governance & Audit
        ("Audit Logs", "/v1/audit/logs", "GET", None),

        # Commerce & Growth
        ("AI Manifest", "/v1/commerce/ai-manifest", "GET", None),
        ("Commerce Catalog", "/v1/commerce/catalog", "GET", None),
        ("Conversational Checkout", "/v1/commerce/conversational-checkout", "POST", {
            "message": "I want to buy Ultra API Gateway",
            "cart": []
        }),
        ("AI-to-AI Buy", "/v1/commerce/ai-buy", "POST", {
            "buyer_agent_id": "DIAG-BOT",
            "spending_token_limit_inr": 100000.0,
            "items": [{"product_id": "PROD-API-01", "quantity": 1}],
            "negotiation_requested": True
        }),
        ("Growth Campaigns List", "/v1/commerce/campaigns", "GET", None),
        ("Failure Sim 1: Timeout", "/v1/commerce/simulate-failure", "POST", {"failure_type": "API_GATEWAY_TIMEOUT"}),
        ("Failure Sim 2: Payload", "/v1/commerce/simulate-failure", "POST", {"failure_type": "INVALID_PAYLOAD"}),
        ("Failure Sim 3: Budget Cap", "/v1/commerce/simulate-failure", "POST", {"failure_type": "BUDGET_CAP_BREACH"}),
        ("Failure Sim 4: Token Limit", "/v1/commerce/simulate-failure", "POST", {"failure_type": "TOKEN_SPENDING_OVERAGE"}),
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
    print(f"DIAGNOSTIC SUMMARY: {passed} PASSED, {failed} FAILED (Total: {len(endpoints)})")
    print("==================================================================")

if __name__ == "__main__":
    run_diagnostics()
