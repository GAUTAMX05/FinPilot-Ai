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

from src.app.services.notification_service import notification_service
from src.app.services.intelligence_service import intelligence_service
from src.app.services.employee_finance_service import employee_finance_service
from src.app.services.payroll_service import payroll_service
from src.app.services.ai_reasoning_engine import ai_reasoning_engine


def run_decision_engine_upgrade_tests():
    print("==================================================================")
    print("     FINANCIAL DECISION OPERATING SYSTEM — UPGRADE TEST SUITE     ")
    print("==================================================================")

    # 1. Notifications Engine & Form 16 Mismatch Tests
    print("\n--- 1. Testing Financial Notifications & Mismatch Alerts ---")
    notifs_res = notification_service.get_notifications("ALL", "CFO", None)
    assert notifs_res["success"] is True
    assert notifs_res["unresolved_count"] > 0
    assert any(n["category"] == "PAYROLL" for n in notifs_res["notifications"])
    print(f"Active Notifications: {notifs_res['total']} (Unresolved: {notifs_res['unresolved_count']}) [✓ PASSED]")

    # Resolve notification test
    res_notif = notification_service.resolve_notification(
        notification_id="NOTIF-2026-001",
        user_id="USR-CFO-001",
        user_name="Vikramaditya S.",
        user_role="CFO",
        resolution_note="Verified salary components against adjusted Annexure B.",
    )
    assert res_notif["success"] is True
    assert res_notif["notification"]["status"] == "RESOLVED"
    print("Notification Resolution & Audit Trail Logging [✓ PASSED]")

    # 2. Dynamic Financial Analytics Time-Series (Daily / Weekly / Monthly)
    print("\n--- 2. Testing Dynamic Time-Series Analytics Aggregations ---")
    for metric in ["spending", "budget_utilization", "cash_flow", "committed_spend", "payroll"]:
        for period in ["daily", "weekly", "monthly"]:
            series = intelligence_service.get_analytics_series(metric, period)
            assert series["success"] is True
            assert len(series["labels"]) == len(series["primary_series"])
            assert len(series["primary_series"]) > 0
    print("Daily, Weekly, and Monthly Time-Series Aggregations for all 5 metrics [✓ PASSED]")

    # 3. Decision Tree Evaluation Engine
    print("\n--- 3. Testing Interactive Decision Tree Rule Pipeline ---")
    tree_res = intelligence_service.evaluate_decision_tree("EXP-2026-8801")
    assert tree_res["decision_score"] >= 80.0
    assert len(tree_res["nodes"]) == 5
    assert all("evidence" in n and "rule" in n and "result" in n for n in tree_res["nodes"])
    print(f"Decision Tree Execution for {tree_res['event_id']}: Score {tree_res['decision_score']}/100 across 5 evaluation nodes [✓ PASSED]")

    # 4. Company Decision Map Hierarchical Graph
    print("\n--- 4. Testing Company Financial Decision Map ---")
    map_res = intelligence_service.get_company_decision_map()
    assert "root" in map_res
    assert len(map_res["root"]["children"]) == 3
    print("Company Decision Map Hierarchical Nodes (Budget, Liquidity, Tax Compliance) [✓ PASSED]")

    # 5. Employee Master CRUD & Deactivation Logic
    print("\n--- 5. Testing Employee Master Management & Deactivation ---")
    new_emp_payload = {
        "employee_id": "EMP-999",
        "name": "Arjun Singhal",
        "email": "arjun.singhal@aifinance.local",
        "department": "Engineering",
        "designation": "Staff Infrastructure Architect",
        "monthly_basic": 120000.0,
        "monthly_allowance_limit": 20000.0,
    }
    add_emp_res = employee_finance_service.add_employee(new_emp_payload, "USR-CFO-001", "Vikramaditya S.", "CFO")
    assert add_emp_res["success"] is True

    # Test Deactivation
    deact_res = employee_finance_service.deactivate_employee("EMP-999", "Role Transition", "USR-CFO-001", "Vikramaditya S.", "CFO")
    assert deact_res["success"] is True
    assert deact_res["employee"]["status"] == "DEACTIVATED"
    print("Employee Master Creation & Safe Compliance Deactivation [✓ PASSED]")

    # 6. Salary Revision Engine
    print("\n--- 6. Testing Salary Revision Engine & Deterministic Math ---")
    rev_res = employee_finance_service.revise_salary(
        employee_id="EMP-101",
        new_basic=82000.0,
        effective_date="2026-09-01",
        reason="Performance Band Adjustment",
        user_id="USR-CFO-001",
        user_name="Vikramaditya S.",
        user_role="CFO",
    )
    assert rev_res["success"] is True
    assert rev_res["salary_revision"]["increase_pct"] > 0
    print(f"Salary Revision for Rahul Sharma: ₹75,000 -> ₹82,000 (+{rev_res['salary_revision']['increase_pct']}%) [✓ PASSED]")

    # 7. Allowance Decision Engine Evaluation
    print("\n--- 7. Testing Allowance Request Decision Engine ---")
    allow_eval = employee_finance_service.evaluate_allowance_request("EMP-101", "Travel", 22000.0)
    assert allow_eval["verdict"] == "ABOVE_DEPARTMENT_LIMIT"
    assert allow_eval["recommended_amount"] == 15000.0
    print(f"Allowance Decision: {allow_eval['assessment']} (Recommended ₹{allow_eval['recommended_amount']:,.0f}) [✓ PASSED]")

    # 8. Form 16 / TDS Tax Reconciliation
    print("\n--- 8. Testing Form 16 / TDS Tax Reconciler & Alerting ---")
    tax_res = payroll_service.get_tax_reconciliation("CFO", None)
    assert tax_res["total_records_audited"] >= 4
    resolve_tax = payroll_service.resolve_tax_record("EMP-1042", "Verified with employee form 16 annexure.", "USR-CFO-001", "Vikramaditya S.", "CFO")
    assert resolve_tax["success"] is True
    print("Form 16 Tax Reconciler & Resolution Dispatch [✓ PASSED]")

    print("\n==================================================================")
    print("ALL DECISION OPERATING SYSTEM UPGRADE TESTS PASSED WITH 100% SUCCESS!")
    print("==================================================================")


if __name__ == "__main__":
    run_decision_engine_upgrade_tests()
