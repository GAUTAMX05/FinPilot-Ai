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

from src.app.services.ai_reasoning_engine import ai_reasoning_engine
from src.app.services.auth_service import auth_service


def run_chat_tests():
    print("==================================================================")
    print("      FINPILOT AI — COMPREHENSIVE REASONING PIPELINE TEST")
    print("==================================================================")

    # Test 1: Overspending Analysis
    print("\n--- TEST 1: Are we overspending? ---")
    res1 = ai_reasoning_engine.analyze_financial_query(
        query="Are we overspending? Analyze all department run-rates vs time elapsed in fiscal year.",
        user_role="CFO",
        user_name="Vikramaditya Singhania",
    )
    assert res1["response"] != "Request processed."
    assert "AI Overspending" in res1["response"]
    assert "Engineering" in res1["response"]
    assert len(res1.get("suggested_actions", [])) > 0
    print(res1["response"][:300] + "...\n[✓ PASSED]")

    # Test 2: Affordability Simulation
    print("\n--- TEST 2: Can we afford ₹500,000 for Engineering? ---")
    res2 = ai_reasoning_engine.analyze_financial_query(
        query="Can we afford another ₹500,000 cloud infrastructure expense for Engineering?",
        user_role="CFO",
        user_name="Vikramaditya Singhania",
    )
    assert res2["response"] != "Request processed."
    assert "Affordability Analysis" in res2["response"]
    assert "500,000" in res2["response"]
    print(res2["response"][:300] + "...\n[✓ PASSED]")

    # Test 3: Department Risk Ranking
    print("\n--- TEST 3: Which department is most at risk? ---")
    res3 = ai_reasoning_engine.analyze_financial_query(
        query="Which department is most at risk?",
        user_role="CFO",
        user_name="Vikramaditya Singhania",
    )
    assert res3["response"] != "Request processed."
    assert "Department Risk Hierarchy" in res3["response"]
    print(res3["response"][:300] + "...\n[✓ PASSED]")

    # Test 4: Department Deep Dive
    print("\n--- TEST 4: Why is Engineering overspending? ---")
    res4 = ai_reasoning_engine.analyze_financial_query(
        query="Why is Engineering overspending?",
        user_role="CFO",
        user_name="Vikramaditya Singhania",
    )
    assert res4["response"] != "Request processed."
    assert "Engineering" in res4["response"]
    print(res4["response"][:300] + "...\n[✓ PASSED]")

    # Test 5: Invoice Anomalies
    print("\n--- TEST 5: Find suspicious invoices ---")
    res5 = ai_reasoning_engine.analyze_financial_query(
        query="Find suspicious invoices.",
        user_role="AUDITOR",
        user_name="Kavita Iyer",
    )
    assert res5["response"] != "Request processed."
    assert "Invoice Anomaly" in res5["response"]
    print(res5["response"][:300] + "...\n[✓ PASSED]")

    # Test 6: Watchtower Brief
    print("\n--- TEST 6: Give me today's financial watchtower brief ---")
    res6 = ai_reasoning_engine.analyze_financial_query(
        query="Give me today's financial watchtower brief.",
        user_role="CFO",
        user_name="Vikramaditya Singhania",
    )
    assert res6["response"] != "Request processed."
    assert "Watchtower" in res6["response"]
    print(res6["response"][:300] + "...\n[✓ PASSED]")

    # Test 7: Forecast Year-End Spending
    print("\n--- TEST 7: Forecast our year-end spending ---")
    res7 = ai_reasoning_engine.analyze_financial_query(
        query="Forecast our year-end spending.",
        user_role="CFO",
        user_name="Vikramaditya Singhania",
    )
    assert res7["response"] != "Request processed."
    assert "Forecast" in res7["response"]
    print(res7["response"][:300] + "...\n[✓ PASSED]")

    # Test 8: Cost Reduction Strategy
    print("\n--- TEST 8: How can we reduce spending? ---")
    res8 = ai_reasoning_engine.analyze_financial_query(
        query="How can we reduce spending?",
        user_role="CFO",
        user_name="Vikramaditya Singhania",
    )
    assert res8["response"] != "Request processed."
    assert "Cost Optimization" in res8["response"]
    print(res8["response"][:300] + "...\n[✓ PASSED]")

    # Test 9: RBAC Guardrail (Dept Head asking for Marketing)
    print("\n--- TEST 9: RBAC Policy Boundary (Dept Head asks for Marketing) ---")
    res9 = ai_reasoning_engine.analyze_financial_query(
        query="Show me Marketing department budget and spending.",
        user_role="DEPARTMENT_HEAD",
        user_name="Priya Verma",
        user_department="Engineering",
    )
    assert "Access Restricted" in res9["response"]
    assert "Engineering" in res9["response"]
    print(res9["response"][:300] + "...\n[✓ PASSED]")

    print("\n==================================================================")
    print("ALL 9 AI CHAT PIPELINE TEST CASES PASSED WITH 100% SUCCESS!")
    print("==================================================================")


if __name__ == "__main__":
    run_chat_tests()
