# -*- coding: utf-8 -*-
"""
============================================================================
FINPILOT AI — COPILOT WHAT-IF REGRESSION TEST
============================================================================
Guards against the "canned Copilot response" regression where
POST /v1/agent/chat returned the identical generic fallback text
("Data retrieved and evaluated against company ledgers... / ...within
safe budget guidelines.") for every what-if scenario.

Root cause was an AttributeError ('dict' object has no attribute 'upper')
in the chat endpoint: the orchestrator returns {"response": {"text": ...}}
but the endpoint treated it as a string, so EVERY successful call fell
into the except branch. This suite fails if that ever regresses, and
additionally pins scenario-specific grounding (parsed headcount/salary/
horizon must appear as computed figures in the reply).
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
from src.app.services.digital_twin_service import digital_twin_service

client = TestClient(app)

CANNED_TEXT = "Data retrieved and evaluated against company ledgers"
CANNED_POLICY = "All operations within safe budget guidelines"

BURN_PROMPT = "What if Engineering spending rate stays the same for 60 more days?"
HIRE_PROMPT = "What if we hire 3 senior engineers in Q3 at Rs.90000 monthly basic?"
EXTREME_PROMPT = "What if we hire 30 senior engineers at Rs.200000 monthly basic for 200 days?"


def _cfo_headers() -> dict:
    user = auth_service.get_user_by_email("cfo@aifinance.local")
    token = create_access_token({"id": user["id"], "role": user["role"], "name": user["name"]})
    return {"Authorization": f"Bearer {token}"}


def _chat(message: str) -> str:
    res = client.post("/v1/agent/chat", json={"message": message, "thread_id": "t-regression"}, headers=_cfo_headers())
    assert res.status_code == 200, f"chat endpoint failed: {res.status_code} {res.text[:200]}"
    body = res.json()
    assert isinstance(body.get("response"), str), (
        f"chat response must be a string, got {type(body.get('response')).__name__}"
    )
    return body["response"]


def test_burn_and_hire_responses_are_distinct_and_grounded():
    """The two bug-report prompts must not return identical boilerplate."""
    burn_text = _chat(BURN_PROMPT)
    hire_text = _chat(HIRE_PROMPT)

    assert CANNED_TEXT not in burn_text
    assert CANNED_TEXT not in hire_text
    assert CANNED_POLICY not in burn_text
    assert CANNED_POLICY not in hire_text
    assert burn_text != hire_text, "Distinct scenarios returned identical text (canned-response regression)"

    # Burn scenario must echo its horizon and computed burn arithmetic
    assert "60 days" in burn_text
    assert "60-day projected spend" in burn_text
    assert "1.12x" in burn_text

    # Hiring scenario must echo the ASKED salary (90000), not a hardcoded default,
    # including the exact monthly-basic arithmetic 3 x 90000 = 270,000
    assert "90,000" in hire_text
    assert "270,000" in hire_text
    print("[PASSED] burn vs hire: distinct, grounded responses")


def test_extreme_scenario_gets_different_policy_status():
    """A genuinely unaffordable what-if must not share the mild-case verdict."""
    mild_text = _chat(HIRE_PROMPT)
    extreme_text = _chat(EXTREME_PROMPT)

    assert "30" in extreme_text and "200,000" in extreme_text
    assert "6,000,000" in extreme_text  # 30 x 200000 monthly basic
    assert "DEFICIT RISK" in extreme_text
    assert "DEFICIT RISK" not in mild_text
    print("[PASSED] extreme scenario escalates to DEFICIT RISK")


def test_scenario_parser_extracts_real_numbers():
    """Unit-pins the parser: no substring digit matching, no ignored salary."""
    hire = digital_twin_service.run_what_if_scenario(HIRE_PROMPT)
    assert hire["action"]["headcount"] == 3
    assert hire["action"]["avg_salary"] == 90000.0

    extreme = digital_twin_service.run_what_if_scenario(EXTREME_PROMPT)
    assert extreme["action"]["headcount"] == 30, f"got {extreme['action']['headcount']}"
    assert extreme["action"]["avg_salary"] == 200000.0

    burn = digital_twin_service.run_what_if_scenario(BURN_PROMPT)
    assert burn["action"]["department"] == "Engineering"
    assert burn["horizon_days"] == 60
    assert burn["action"]["horizon_days"] == 60
    print("[PASSED] parser extracts headcount/salary/horizon exactly")


FIRE_PROMPT = "What if we fire 4 engineer"


def test_fire_scenario_reduces_payroll_not_expense():
    """Firing must parse as negative headcount (saving), never as an expense."""
    fire = digital_twin_service.run_what_if_scenario(FIRE_PROMPT)
    assert fire["action"]["headcount"] == -4, f"got {fire['action']['headcount']}"
    assert fire["deltas"]["liquidity_change"] > 0, "firing must improve liquidity"

    text = _chat(FIRE_PROMPT)
    assert "Reduce 4" in text
    assert "340,000" in text  # 4 x 85000 default basic
    assert "Disburse planned expense" not in text
    assert "tightens liquidity runway" not in text
    print("[PASSED] firing reduces payroll; no fabricated expense")


RECV_PROMPT = "What if a major client delays payment by 45 days?"


def test_runway_math_matches_hand_computation():
    """Step-5 pin: runway = first day cash breaches threshold, hand-verified."""
    from src.app.services.digital_twin_service import digital_twin_service as twin
    state = twin.get_live_state(force_refresh=True)
    cash = float(state["cash_position"]["liquid_reserves"])
    safe = float(state["cash_position"]["safe_liquidity_threshold"])
    inflow = float(state["cash_position"]["inflows_daily_avg"])
    daily_out = (float(state["budget_position"]["total_monthly_burn"])
                 + float(state["payroll_position"]["monthly_gross_total"])) / 30.0
    c, expected_breach = cash, None
    for day in range(1, 91):
        c += inflow
        c -= daily_out
        if expected_breach is None and c < safe:
            expected_breach = day
            break
    sim = twin.simulate_forward(days=90, modifiers={})
    assert expected_breach is not None and expected_breach > 1
    assert sim["cash_breach_day"] == expected_breach, (
        f"fn={sim['cash_breach_day']} hand={expected_breach}")
    assert sim["projected_runway_days"] == expected_breach
    print(f"[PASSED] runway matches hand computation (breach day {expected_breach})")


def test_runway_moves_with_scenario_direction():
    """Savings must extend runway; massive hiring must shorten it. Never 1->1."""
    from src.app.services.digital_twin_service import digital_twin_service as twin
    base = twin.simulate_forward(days=90, modifiers={})
    fire = twin.run_what_if_scenario("What if we fire 4 engineer")
    assert fire["after"]["runway_days"] >= base["projected_runway_days"], (
        "firing must not shorten runway")
    extreme = twin.run_what_if_scenario(
        "What if we hire 30 senior engineers at Rs.200000 monthly basic for 200 days?")
    assert extreme["after"]["runway_days"] < base["projected_runway_days"], (
        "mass hiring must shorten runway")
    print("[PASSED] runway moves with scenario direction")


def test_client_payment_delay_is_receivables_not_expense():
    """A client paying late holds INFLOWS (opposite of a vendor delay)."""
    from src.app.services.digital_twin_service import digital_twin_service as twin
    recv = twin.run_what_if_scenario(RECV_PROMPT)
    assert recv["action"]["type"] == "RECEIVABLE_DELAY", recv["action"]
    assert recv["action"]["days"] == 45
    assert recv["deltas"]["liquidity_change"] < 0, "held inflows must hurt liquidity"
    text = _chat(RECV_PROMPT)
    assert "receivable" in text.lower()
    assert "45 days" in text
    assert "Disburse planned expense" not in text
    print("[PASSED] client delay modeled as inflow hold")


def test_reasoning_quick_buttons_all_distinct():
    """All five Reasoning Queries quick-buttons must return distinct grounded text."""
    prompts = [
        "What if Engineering spending rate stays the same for 60 more days?",
        "What if we delay vendor payments by 2 weeks - does it fix our cash position?",
        "What if we hire 3 senior engineers in Q3 at Rs.90000 monthly basic?",
        "Why is Engineering overspending on cloud? Pinpoint causal root cause.",
        "Assess company liquidity runway and statutory compliance health",
    ]
    texts = [_chat(p) for p in prompts]
    for t in texts:
        assert CANNED_TEXT not in t
        assert len(t) > 200
    assert len(set(texts)) == len(texts), "Two quick-buttons returned identical text"
    print("[PASSED] all 5 quick-buttons distinct and grounded")


if __name__ == "__main__":
    test_burn_and_hire_responses_are_distinct_and_grounded()
    test_extreme_scenario_gets_different_policy_status()
    test_scenario_parser_extracts_real_numbers()
    test_fire_scenario_reduces_payroll_not_expense()
    test_runway_math_matches_hand_computation()
    test_runway_moves_with_scenario_direction()
    test_client_payment_delay_is_receivables_not_expense()
    test_reasoning_quick_buttons_all_distinct()
    print("ALL COPILOT WHAT-IF REGRESSION TESTS PASSED")
