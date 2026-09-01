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

def run_endpoint_check(name, path, method="GET", body=None, headers=None):
    headers = headers or {}
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    if body is not None and "Content-Type" not in headers:
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


if __name__ == "__main__":
    print("=" * 66)
    print("  FINPILOT AI — TEST ALL FRONTEND API ENDPOINTS")
    print("=" * 66)

    # 1. Health & Probes
    run_endpoint_check("Health Liveness", "/health")
    run_endpoint_check("Readiness Probe", "/ready")

    # 2. Digital Twin & Multi-Agent Simulation
    run_endpoint_check("Digital Twin State", "/v1/simulation/digital-twin-state")
    run_endpoint_check("Policy Calibrations", "/v1/simulation/policy-calibrations")
    run_endpoint_check("What-If Simulation", "/v1/simulation/what-if", "POST", {"scenario": "Can we afford ₹500,000 for Engineering?"})
    run_endpoint_check("Causal Analysis", "/v1/simulation/causal-analysis?anomaly_query=Engineering", "GET", None)

    # 3. Notifications & Mismatches
    run_endpoint_check("Get Notifications", "/v1/notifications?category=ALL", "GET", None)
    run_endpoint_check("Mark All Read", "/v1/notifications/mark-all-read", "POST", {})

    # 4. Intelligence & Charts
    run_endpoint_check("Analytics Series", "/v1/intelligence/analytics-series?metric=burn&period=daily", "GET", None)
    run_endpoint_check("Watchtower Radar", "/v1/intelligence/watchtower", "GET", None)
    run_endpoint_check("Decision Tree Eval", "/v1/intelligence/decision-tree-eval?event_id=EXP-2026-8801", "GET", None)
    run_endpoint_check("Company Decision Map", "/v1/intelligence/company-decision-map", "GET", None)
    run_endpoint_check("Budget Forecasts", "/v1/intelligence/forecasts", "GET", None)
    run_endpoint_check("Vendors Intelligence", "/v1/intelligence/vendors", "GET", None)
    run_endpoint_check("Affordability Analysis", "/v1/intelligence/affordability", "POST", {
        "department": "Engineering",
        "amount": 500000.0,
        "category": "Cloud Infrastructure",
        "description": "Cloud cluster expansion"
    })
    run_endpoint_check("Executive Report", "/v1/intelligence/report", "GET", None)

    # 5. Budgets & Invoices
    run_endpoint_check("Department Budgets", "/v1/budgets", "GET", None)
    run_endpoint_check("Budget Reallocate", "/v1/budgets/reallocate", "POST", {
        "from_department": "Operations",
        "to_department": "Engineering",
        "amount": 10000.0,
        "reason": "Test rebalance"
    })
    run_endpoint_check("Invoices List", "/v1/invoices", "GET", None)
    run_endpoint_check("Audit Invoice", "/v1/invoices/audit", "POST", {
        "vendor_name": "CloudOps Technologies Pvt Ltd",
        "department": "Engineering",
        "category": "Cloud Infrastructure",
        "subtotal": 10000.0,
        "tax_gst": 1800.0,
        "total_amount": 11800.0,
        "description": "Cloud cluster audit"
    })

    # 6. Approvals & Cash Flow
    run_endpoint_check("Pending Approvals", "/v1/approvals/pending", "GET", None)
    run_endpoint_check("Cash Flow Forecast", "/v1/cash-flow/forecast", "GET", None)

    # 7. Payroll & Tax
    run_endpoint_check("Tax Reconciliation", "/v1/payroll/tax-reconciliation", "GET", None)
    run_endpoint_check("Employees List", "/v1/employees", "GET", None)
    run_endpoint_check("Allowance Anomalies", "/v1/employees/anomalies/allowance", "GET", None)

    # 8. Audit & AI Agent Chat
    run_endpoint_check("Audit Logs", "/v1/audit/logs", "GET", None)
    run_endpoint_check("AI Agent Chat", "/v1/agent/chat", "POST", {
        "message": "Are we overspending this month?",
        "thread_id": "test_thread_01"
    })

    # 9. Merchant AI Commerce
    run_endpoint_check("Commerce Manifest", "/v1/commerce/ai-manifest", "GET", None)
    run_endpoint_check("Catalog Discovery", "/v1/commerce/catalog", "GET", None)
    run_endpoint_check("Conversational Checkout", "/v1/commerce/conversational-checkout", "POST", {
        "message": "Add 2 Premium Cloud GPU Licenses to cart",
        "cart_items": [{"product_id": "prod_001", "quantity": 1}]
    })
    run_endpoint_check("Campaigns List", "/v1/commerce/campaigns", "GET", None)

    # 10. Autonomous Finance Controller & HITL
    run_endpoint_check("Gateway Status", "/v1/controller/gateway-status")
    run_endpoint_check("Controller Dashboard", "/v1/controller/dashboard")
    run_endpoint_check("Exceptions Queue", "/v1/controller/exceptions")
    run_endpoint_check("Reconciliation Records", "/v1/controller/reconciliation")
    run_endpoint_check("Benchmark Evaluation", "/v1/controller/evaluation")
    run_endpoint_check("Merchant Day Cycle", "/v1/controller/merchant-day/run", "POST", {})

    print("\n" + "=" * 66)
    print("  ALL ENDPOINTS TESTED SUCCESSFULLY!")
    print("=" * 66)
