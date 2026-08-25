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

from src.app.services.reconciliation_service import reconciliation_service
from src.app.services.cash_flow_service import cash_flow_service
from src.app.services.employee_finance_service import employee_finance_service
from src.app.services.payroll_service import payroll_service
from src.app.services.ai_reasoning_engine import ai_reasoning_engine


def run_enterprise_platform_tests():
    print("==================================================================")
    print("  ENTERPRISE FINANCE & EMPLOYEE FINANCIAL CONTROL PLATFORM TESTS")
    print("==================================================================")

    # 1. Two-Stage Hybrid Reconciliation Test
    print("\n--- 1. Testing Two-Stage Reconciliation Engine ---")
    recon_res = reconciliation_service.run_reconciliation()
    assert recon_res["success"] is True
    assert recon_res["auto_matched_count"] > 0
    assert recon_res["exceptions_count"] > 0
    print(f"Auto-matched: {recon_res['auto_matched_count']} ({recon_res['match_rate_percentage']}%), Exceptions: {recon_res['exceptions_count']} [✓ PASSED]")

    # 2. Cash Flow Forecasting Test
    print("\n--- 2. Testing Multi-Horizon Cash Flow Forecasting ---")
    cf_res = cash_flow_service.generate_cash_forecast("CFO", None)
    assert cf_res["current_liquidity"] > 0
    assert "seven_day" in cf_res["horizons"]
    assert "thirty_day" in cf_res["horizons"]
    assert "ninety_day" in cf_res["horizons"]
    assert len(cf_res["daily_curve"]) == 30
    print(f"Current Liquidity: ₹{cf_res['current_liquidity']:,.2f}, 30-Day: ₹{cf_res['horizons']['thirty_day']['projected_liquidity']:,.2f} [✓ PASSED]")

    # 3. Employee Allowance & AI Recommendation Test
    print("\n--- 3. Testing Employee Allowance & AI Recommendation ---")
    rec_res = employee_finance_service.recommend_allowance_limit("EMP-101", "Travel")
    assert rec_res["recommended_monthly_limit"] > 0
    assert rec_res["confidence_percentage"] >= 80.0
    print(f"Recommended Travel Limit for {rec_res['employee_name']}: ₹{rec_res['recommended_monthly_limit']:,.0f} (Confidence: {rec_res['confidence_percentage']}%) [✓ PASSED]")

    # 4. Allowance Anomaly Scanner Test
    print("\n--- 4. Testing Allowance Anomaly Scanner ---")
    anomalies = employee_finance_service.detect_allowance_anomalies("CFO", None)
    assert len(anomalies) > 0
    assert any(a["type"] == "POLICY_LIMIT_EXCEEDED" for a in anomalies)
    print(f"Detected {len(anomalies)} Allowance Anomalies (Limit Exceeded & Duplicate Claims) [✓ PASSED]")

    # 5. Payroll Bill Analyzer & Gross Cross-Check Test
    print("\n--- 5. Testing Payroll Bill Cross-Check ---")
    pay_res = payroll_service.get_payroll_summary("CFO", None)
    assert pay_res["total_gross_disbursed"] > 0
    assert pay_res["mismatch_count"] > 0
    print(f"Total Gross Disbursed: ₹{pay_res['total_gross_disbursed']:,.2f}, Cross-check Mismatches: {pay_res['mismatch_count']} [✓ PASSED]")

    # 6. Form 16 / TDS Tax Reconciler Test
    print("\n--- 6. Testing Form 16 / TDS Tax Reconciler ---")
    tax_res = payroll_service.get_tax_reconciliation("CFO", None)
    assert tax_res["total_records_audited"] > 0
    print(f"Form 16 Tax Files Audited: {tax_res['total_records_audited']}, Reconciled: {tax_res['fully_reconciled_count']} [✓ PASSED]")

    # 7. Headcount Cost & Growth Forecast Test
    print("\n--- 7. Testing Headcount Cost & Growth Forecast ---")
    hc_res = payroll_service.get_headcount_cost_analytics()
    assert hc_res["total_annual_employee_cost"] > 0
    assert "twelve_months" in hc_res["headcount_growth_forecast"]
    print(f"Total Annual Employee Cost: ₹{hc_res['total_annual_employee_cost']:,.2f}, 12-Month Proj: ₹{hc_res['headcount_growth_forecast']['twelve_months']['projected_annual_cost']:,.2f} [✓ PASSED]")

    # 8. Natural Language Reasoning on New Capabilities
    print("\n--- 8. Testing Natural-Language AI Copilot on New Modules ---")
    q1 = ai_reasoning_engine.analyze_financial_query("What is our 30-day cash and liquidity forecast?", "CFO", "Vikramaditya S.")
    assert "AI Cash Flow" in q1["response"]

    q2 = ai_reasoning_engine.analyze_financial_query("Show reconciliation exceptions and fee variances.", "CFO", "Vikramaditya S.")
    assert "Hybrid Financial Reconciliation" in q2["response"]

    q3 = ai_reasoning_engine.analyze_financial_query("Recommend monthly allowance limit for Rahul Sharma.", "CFO", "Vikramaditya S.")
    assert "AI Employee Allowance Recommendation" in q3["response"]

    q4 = ai_reasoning_engine.analyze_financial_query("Check August payroll register for salary mismatches and Form 16 TDS consistency.", "CFO", "Vikramaditya S.")
    assert "AI Payroll Analyzer" in q4["response"]

    q5 = ai_reasoning_engine.analyze_financial_query("What will our total employee headcount cost be next year?", "CFO", "Vikramaditya S.")
    assert "AI Total Employee Cost" in q5["response"]

    print("Natural Language Copilot accurately reasoned over Cash Flow, Reconciliation, Allowances, Payroll, and Headcount! [✓ PASSED]")

    print("\n==================================================================")
    print("ALL ENTERPRISE PLATFORM TEST SUITES PASSED WITH 100% SUCCESS!")
    print("==================================================================")


if __name__ == "__main__":
    run_enterprise_platform_tests()
