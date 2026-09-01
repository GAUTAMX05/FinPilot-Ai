import sys
import os
import unittest

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.app.services.digital_twin_service import digital_twin_service
from src.app.services.merchant_commerce_service import merchant_commerce_service
from src.app.services.audit_service import audit_service
from src.app.services.multi_agent_orchestrator import MultiAgentFinancialOrchestrator


class TestAIJudgmentAndDeterministicGuardrails(unittest.TestCase):
    """
    Validates the core 'AI Judgment' principle:
    - Smart use of autonomous AI agents for high-dimensional reasoning, synthesis,
      counterfactual what-if simulation, and natural language cart parsing.
    - Zero delegation of ledger arithmetic, security checks, cryptographic hashing,
      and policy limits to probabilistic LLM tokens (knowing when NOT to use AI).
    """

    def setUp(self):
        self.orchestrator = MultiAgentFinancialOrchestrator()

    def test_deterministic_tax_and_ledger_arithmetic_never_hallucinates(self):
        """
        AI Judgment: Statutory 18% GST, subtotals, and discounts must be calculated
        via deterministic Python arithmetic, NEVER probabilistic LLM token generation.
        """
        cart = [
            {"product_id": "PROD-API-01", "quantity": 2},     # 2 * 12,500 = 25,000
            {"product_id": "PROD-VPC-02", "quantity": 1},     # 1 * 28,000 = 28,000
        ]
        # Subtotal: 53,000. GST (18%): 9,540. Total: 62,540.
        res = merchant_commerce_service.process_conversational_checkout(
            message="Calculate checkout breakdown",
            cart=cart
        )
        summary = res["cart_summary"]
        self.assertEqual(summary["subtotal"], 53000.0, "Subtotal must be exact float sum")
        self.assertEqual(summary["gst_amount"], 9540.0, "GST must be exact 18% calculation")
        self.assertEqual(summary["total_amount"], 62540.0, "Total must equal subtotal + GST exactly")

    def test_hard_spending_token_limit_enforced_before_agent_action(self):
        """
        AI Judgment: Spending ceilings and token bounds are non-negotiable hard guards.
        Even if an AI buyer requests a transaction, it is aborted if token ceiling is breached.
        """
        # Buyer authorized token limit: ₹25,000. Attempted buy: 1 unit of Dedicated VPC (₹28,000 + GST = ₹33,040).
        res = merchant_commerce_service.process_ai_to_ai_purchase(
            buyer_agent_id="Agent-Buyer-Alpha",
            spending_token_limit_inr=25000.0,  # Below required total
            requested_items=[{"product_id": "PROD-VPC-02", "quantity": 1}],
            negotiation_requested=False,
        )
        self.assertFalse(res["success"], "Transaction MUST be rejected when exceeding hard token limit")
        self.assertEqual(res["error_code"], "SPENDING_TOKEN_LIMIT_EXCEEDED")
        self.assertIn("exceeds Buyer Agent Spending Token Limit", res["detail"])

    def test_deterministic_digital_twin_forward_simulation(self):
        """
        AI Judgment: Financial Digital Twin 90-day simulation uses exact step-by-step
        differential math rather than speculative text generation.
        """
        sim = digital_twin_service.simulate_forward(
            days=90,
            modifiers={
                "dept_burn_multipliers": {"Engineering": 1.10},
                "payment_delay_days": 14,
            }
        )
        self.assertIn("cash_trajectory", sim)
        self.assertEqual(sim["simulation_days"], 90)
        self.assertTrue(len(sim["cash_trajectory"]) >= 10, "Must contain sampled cash trajectory points")
        self.assertIn("final_liquidity", sim)
        self.assertTrue(sim["projected_runway_days"] > 0, "Runway calculation must be valid")

    def test_smart_ai_usage_role_aware_semantic_synthesis(self):
        """
        AI Judgment: AI agents ARE used for high-dimensional semantic analysis,
        cross-functional root-cause correlation, and role-tailored explanations.
        """
        cfo_res = self.orchestrator.process_query(
            query="Why is Engineering spending increasing and what should be done?",
            user_role="CFO",
            user_name="Vikramaditya Singhania",
        )
        auditor_res = self.orchestrator.process_query(
            query="Why is Engineering spending increasing and what should be done?",
            user_role="AUDITOR",
            user_name="Kavita Iyer",
        )

        cfo_text = cfo_res.get("response", {}).get("text", "") if isinstance(cfo_res.get("response"), dict) else str(cfo_res.get("response", ""))
        auditor_text = auditor_res.get("response", {}).get("text", "") if isinstance(auditor_res.get("response"), dict) else str(auditor_res.get("response", ""))

        self.assertTrue(len(cfo_text) > 100)
        self.assertTrue(len(auditor_text) > 100)
        self.assertTrue(str(cfo_res["trace_id"]).startswith("TRC-"), "Must trace agent execution pipeline")
        
        # Responses contain structured 5-step role-tailored reasoning
        self.assertIn("WHAT HAPPENED", cfo_text.upper())
        self.assertIn("WHY IT MATTERS", cfo_text.upper())
        self.assertIn("WHAT SHOULD BE DONE", cfo_text.upper())

    def test_immutable_audit_hash_chain_integrity(self):
        """
        AI Judgment: Compliance records use deterministic SHA-256 cryptographic
        hash chaining for tamper-evident validation.
        """
        log_entry = audit_service.log_action(
            user_id="usr_cfo_001",
            user_name="Vikramaditya Singhania",
            role="CFO",
            action="POLICY_OVERRIDE_REVIEW",
            entity="BUDGET",
            entity_id="DEPT-ENG",
            details="Reviewed Engineering Q3 expansion justification.",
            risk_level="MEDIUM",
        )
        self.assertTrue("audit_hash" in log_entry, "Every audit record must have SHA-256 hash")
        self.assertEqual(len(log_entry["audit_hash"]), 64, "SHA-256 hash must be exactly 64 hex characters")
        self.assertTrue("prev_hash" in log_entry, "Every audit record must point to previous block hash")


if __name__ == "__main__":
    print("==================================================================")
    print("   FINPILOT AI — AI JUDGMENT & DETERMINISTIC GUARDS TEST SUITE    ")
    print("==================================================================")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAIJudgmentAndDeterministicGuardrails)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n==================================================================")
        print("ALL AI JUDGMENT & DETERMINISTIC GUARD TESTS PASSED 100%!")
        print("==================================================================")
    else:
        sys.exit(1)
