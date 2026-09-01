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

from src.app.services.intelligence_service import intelligence_service
from src.app.services.budget_service import budget_service
from src.app.services.auth_service import auth_service
from src.app.services.audit_service import audit_service
from src.app.tools.finance_tools import (
    get_company_financial_health_score,
    forecast_department_budget,
    simulate_expense_affordability,
    detect_duplicate_invoice_similarity,
    analyze_vendor_risk_profile,
    get_proactive_watchtower_alerts,
    recommend_budget_reallocation,
)


def test_financial_health_score():
    print("1. Testing AI Financial Health Score Engine...")
    health = intelligence_service.calculate_health_score()
    assert "overall_score" in health
    assert 0 <= health["overall_score"] <= 100
    assert "explainability" in health and len(health["explainability"]) >= 4
    assert health["sub_scores"]["liquidity"] > 0
    print(f"✓ Health Score calculated: {health['overall_score']}/100 ({health['rating']})")
    for exp in health["explainability"]:
        print(f"   • {exp}")


def test_budget_forecasting_and_overrun():
    print("\n2. Testing Predictive Budget Forecasting & Overrun Engine...")
    forecasts = intelligence_service.get_department_forecasts()
    assert len(forecasts) >= 5
    
    eng = next((f for f in forecasts if f["department"] == "Engineering"), None)
    assert eng is not None
    assert "projected_year_end_spend" in eng
    assert "monthly_run_rate" in eng
    assert "risk_level" in eng
    print(f"✓ Engineering Forecast: Spent ₹{eng['spent_amount']:,.2f} / Cap ₹{eng['allocated_budget']:,.2f}")
    print(f"   Monthly Run-Rate: ₹{eng['monthly_run_rate']:,.2f}/mo | Projected Year-End: ₹{eng['projected_year_end_spend']:,.2f}")
    print(f"   Risk: {eng['risk_badge']}")


def test_affordability_simulator():
    print("\n3. Testing 'Can We Afford This?' Affordability Simulation Engine...")
    # Safe expense
    safe_sim = intelligence_service.simulate_affordability(
        amount=50000.0,
        department="Engineering",
        category="Software Licenses",
    )
    assert safe_sim["verdict"] in ["APPROVED_SAFE", "CAUTION"]
    print(f"✓ Safe ₹50K Simulation Verdict: {safe_sim['verdict_badge']}")

    # Overrun / large expense
    large_sim = intelligence_service.simulate_affordability(
        amount=4000000.0,
        department="Engineering",
        category="Data Center Expansion",
    )
    assert large_sim["verdict"] in ["BUDGET_EXCEEDED", "INSUFFICIENT_LIQUIDITY", "REJECTED_DEFICIT"]
    print(f"✓ Deficit ₹4M Simulation Verdict: {large_sim['verdict_badge']}")


def test_duplicate_similarity_detection():
    print("\n4. Testing Multi-Vector Duplicate Invoice Similarity Scanner...")
    # Test identical / highly similar invoice
    dup_res = intelligence_service.detect_duplicate_similarity(
        vendor_name="CloudOps Technologies Pvt Ltd",
        amount=100300.0,
        department="Engineering",
        description="Cloud servers",
    )
    print(f"✓ Duplicate Scanner Result: {dup_res['similarity_percentage']}% similarity")
    print(f"   Explanation: {dup_res['explanation']}")


def test_vendor_risk_intelligence():
    print("\n5. Testing Vendor Risk & Spend Intelligence...")
    vendors = intelligence_service.get_vendor_intelligence()
    assert len(vendors) > 0
    top_vendor = vendors[0]
    assert "total_spend" in top_vendor
    assert "risk_score" in top_vendor
    print(f"✓ Top Vendor Exposure: {top_vendor['vendor_name']} | Total Spend: ₹{top_vendor['total_spend']:,.2f} | Risk: {top_vendor['risk_score']}/100 ({top_vendor['status']})")


def test_watchtower_alerts():
    print("\n6. Testing Proactive AI Financial Watchtower Alerts...")
    alerts = intelligence_service.get_watchtower_alerts()
    assert len(alerts) >= 2
    for a in alerts:
        print(f"   [{a['badge']}] {a['title']}: {a['message']}")


def test_ai_proposal_execution():
    print("\n7. Testing AI Actionable Proposal Execution & Audit Trail...")
    proposals = intelligence_service.get_proposals()
    assert len(proposals) > 0
    prop = proposals[0]
    
    # Execute proposal as CFO
    exec_res = intelligence_service.execute_proposal(
        proposal_id=prop["proposal_id"],
        user_id="usr_cfo_01",
        user_name="Vikramaditya Singhania",
        user_role="CFO",
    )
    assert exec_res["success"] is True
    print(f"✓ Executed AI Proposal {prop['proposal_id']}: {prop['title']}")
    
    # Verify Audit Log
    logs = audit_service.get_audit_logs(limit=5)
    last_log = logs[0]
    assert last_log["action"] == "EXECUTE_AI_PROPOSAL"
    print(f"✓ Immutable Audit Log Recorded: {last_log['action']} by {last_log['user_name']} on {last_log['entity_id']}")


if __name__ == "__main__":
    test_financial_health_score()
    test_budget_forecasting_and_overrun()
    test_affordability_simulator()
    test_duplicate_similarity_detection()
    test_vendor_risk_intelligence()
    test_watchtower_alerts()
    test_ai_proposal_execution()
    print("\n==================================================================")
    print("ALL AI FINANCIAL INTELLIGENCE & AUTONOMOUS TESTS PASSED (100% OK)")
    print("==================================================================")
