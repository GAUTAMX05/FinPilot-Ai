import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.app.services.digital_twin_service import digital_twin_service
from src.app.services.multi_agent_orchestrator import multi_agent_orchestrator
from src.app.services.policy_calibration_service import policy_calibration_service


def run_digital_twin_and_agents_tests():
    print("==================================================================")
    print("     FINANCIAL DIGITAL TWIN & MULTI-AGENT TEST SUITE     ")
    print("==================================================================")

    # 1. Digital Twin State Snapshot
    print("\n--- 1. Testing Financial Digital Twin State Snapshot ---")
    state = digital_twin_service.get_live_state(force_refresh=True)
    assert "cash_position" in state
    assert "budget_position" in state
    assert "payroll_position" in state
    assert "decision_score" in state
    assert state["cash_position"]["liquid_reserves"] > 5000000.0
    assert state["decision_score"]["overall_score"] >= 70.0
    print(f"Digital Twin Live Snapshot: Cash=₹{state['cash_position']['liquid_reserves']:,.0f}, Score={state['decision_score']['overall_score']}/100 [✓ PASSED]")

    # 2. Digital Twin Forward Day-by-Day Simulation
    print("\n--- 2. Testing Digital Twin Forward Day-by-Day Simulation ---")
    sim_res = digital_twin_service.simulate_forward(days=90, modifiers={})
    assert sim_res["simulation_days"] == 90
    assert len(sim_res["labels"]) > 5
    assert len(sim_res["cash_trajectory"]) > 5
    print(f"90-Day Forward Simulation: Final Liquidity=₹{sim_res['final_liquidity']:,.0f}, Projected Runway={sim_res['projected_runway_days']} days [✓ PASSED]")

    # 3. Action Simulation Before vs. After Deltas
    print("\n--- 3. Testing Action Simulation Before vs. After Deltas ---")
    action = {
        "type": "EXPENSE",
        "amount": 500000.0,
        "department": "Engineering",
        "description": "Simulate ₹500,000 cloud infrastructure expansion",
    }
    res = digital_twin_service.simulate_action(action)
    assert "before" in res
    assert "after" in res
    assert "deltas" in res
    assert "verdict" in res
    assert res["deltas"]["liquidity_change"] < 0
    print(f"Simulate ₹500K Expense: Liquidity Change=₹{res['deltas']['liquidity_change']:,.0f}, Verdict={res['verdict_badge']} [✓ PASSED]")

    # 4. Multi-Agent Orchestrator Pipeline
    print("\n--- 4. Testing Multi-Agent Orchestrator Pipeline & Hand-offs ---")
    orch_res = multi_agent_orchestrator.process_query(
        query="What if Engineering spending rate stays the same for 60 more days?",
        user_role="CFO",
        user_name="Vikramaditya Singhania",
    )
    assert orch_res["intent"] == "COUNTERFACTUAL_SIMULATION"
    assert len(orch_res["agent_steps"]) >= 5
    assert "WHAT HAPPENED" in orch_res["response"]["formatted_text"]
    assert "WHY IT MATTERS" in orch_res["response"]["formatted_text"]
    print(f"Multi-Agent Pipeline: Trace={orch_res['trace_id']}, Sub-agents executed={len(orch_res['agent_steps'])} [✓ PASSED]")

    # 5. Role-Aware Explainability Depth
    print("\n--- 5. Testing Role-Aware Explainability Depth ---")
    # Auditor test
    aud_res = multi_agent_orchestrator.process_query(
        query="Audit August payroll and Form 16 salary differences",
        user_role="AUDITOR",
        user_name="Kavita Iyer",
    )
    assert "Audit-Grade Multi-Agent Lineage" in aud_res["response"]["formatted_text"]
    assert "Deterministic Rule Verification" in aud_res["response"]["formatted_text"]

    # Dept Head test
    eng_res = multi_agent_orchestrator.process_query(
        query="Can we afford another ₹300,000 for cloud infrastructure?",
        user_role="DEPARTMENT_HEAD",
        user_name="Priya Verma",
        user_department="Engineering",
    )
    assert "Engineering Department Financial Assessment" in eng_res["response"]["formatted_text"]
    print("Role-Aware Explainability: Auditor received raw lineage; Dept Head received scoped assessment [✓ PASSED]")

    # 6. Causal Anomaly Detection
    print("\n--- 6. Testing Causal Anomaly Detection & Signal Correlation ---")
    causal_data = multi_agent_orchestrator._run_causal_correlation("Why is Engineering overspending on cloud?")
    assert causal_data["anomaly_type"] == "BUDGET_RUN_RATE_OVERRUN"
    assert causal_data["confidence"] > 0.85
    assert len(causal_data["correlated_signals"]) > 1
    print(f"Causal Correlation: Root Cause='{causal_data['primary_cause']}' (Confidence: {causal_data['confidence']*100}%) [✓ PASSED]")

    # 7. Self-Calibrating Policy Engine
    print("\n--- 7. Testing Self-Calibrating Policy Engine & Friction Detection ---")
    proposals = policy_calibration_service.get_calibration_proposals()
    assert len(proposals) > 0
    p1 = proposals[0]
    assert p1["target_rule"] == "RULE-ALLOWANCE-TRAVEL"
    assert "approved" in p1["evidence"].lower()

    apply_res = policy_calibration_service.apply_calibration(
        proposal_id=p1["proposal_id"],
        actor_id="usr_cfo_001",
        actor_name="Vikramaditya S.",
        actor_role="CFO",
    )
    assert apply_res["success"] is True
    print(f"Policy Calibration: Proposal='{p1['title']}', Override Evidence='{p1['evidence']}' -> Applied [✓ PASSED]")

    print("\n==================================================================")
    print("ALL DIGITAL TWIN & MULTI-AGENT TESTS PASSED WITH 100% SUCCESS!")
    print("==================================================================")


if __name__ == "__main__":
    run_digital_twin_and_agents_tests()
