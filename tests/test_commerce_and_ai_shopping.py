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

from src.app.services.merchant_commerce_service import merchant_commerce_service
from src.app.services.budget_service import budget_service


def run_commerce_tests():
    print("==================================================================")
    print("   FINPILOT AI — MERCHANT GROWTH & AI COMMERCE TEST SUITE        ")
    print("==================================================================")

    # --- 1. Agent-Readable Manifest & Catalog Discovery ---
    print("\n--- 1. Testing Agent-Readable Manifest & Catalog Discovery ---")
    manifest = merchant_commerce_service.get_agent_manifest()
    assert manifest.get("protocol_version") == "AgentCommerce-v1.0", "Manifest protocol version mismatch"
    assert "catalog_discovery" in manifest["endpoints"], "Catalog endpoint must be advertised"
    assert manifest["autonomous_purchasing_rules"]["max_negotiable_discount_pct"] == 15.0
    print(f"Manifest Generated: Protocol={manifest['protocol_version']}, Merchant={manifest['merchant_name']} [✓ PASSED]")

    catalog = merchant_commerce_service.get_catalog()
    assert catalog["total_items"] >= 5, "Expected at least 5 products in catalog"
    prod_ids = [p["id"] for p in catalog["products"]]
    assert "PROD-API-01" in prod_ids, "PROD-API-01 must be in catalog"
    print(f"Catalog Verified: Total Products={catalog['total_items']} [✓ PASSED]")

    # --- 2. Smart Cross-Sell & Upsell Agent ---
    print("\n--- 2. Testing Smart Upsell Bundle Engine ---")
    cart_with_api = [{"product_id": "PROD-API-01", "quantity": 1}]
    upsell_res = merchant_commerce_service.generate_smart_upsell(cart_with_api)
    assert upsell_res["has_upsell"] is True, "Expected smart upsell recommendation for PROD-API-01"
    top_rec = upsell_res["recommendations"][0]
    assert top_rec["upsell_product_id"] == "PROD-VPC-02"
    assert top_rec["bundle_discount_pct"] == 15.0
    assert top_rec["customer_savings"] > 0
    print(f"Smart Upsell Generated: Bundle='{top_rec['bundle_name']}', Savings=₹{top_rec['customer_savings']:,.2f} [✓ PASSED]")

    # --- 3. Conversational In-App Checkout & Dynamic Cart ---
    print("\n--- 3. Testing Conversational In-App Checkout ---")
    conv1 = merchant_commerce_service.process_conversational_checkout(
        message="I want to buy the Ultra API Gateway",
        cart=[]
    )
    assert len(conv1["cart"]) == 1, "Expected 1 item in cart"
    assert conv1["cart_summary"]["subtotal"] == 12500.0
    assert conv1["cart_summary"]["gst_amount"] == 2250.0  # 18% of 12500
    assert conv1["cart_summary"]["total_amount"] == 14750.0
    print(f"Conversational Add: Subtotal=₹{conv1['cart_summary']['subtotal']:,.2f}, Total=₹{conv1['cart_summary']['total_amount']:,.2f} [✓ PASSED]")

    # Trigger checkout
    conv2 = merchant_commerce_service.process_conversational_checkout(
        message="Confirm and proceed to pay now",
        cart=conv1["cart"],
        execute_checkout=True
    )
    assert conv2["checkout_details"] is not None, "Expected checkout details"
    assert conv2["checkout_details"]["status"] == "AWAITING_PAYMENT"
    assert "payment_url" in conv2["checkout_details"]
    print(f"Razorpay Checkout Link Generated: URL={conv2['checkout_details']['payment_url']} [✓ PASSED]")

    # --- 4. Autonomous AI-to-AI Shopping & Bounded Negotiation ---
    print("\n--- 4. Testing Autonomous AI-to-AI Shopping & Negotiation ---")
    a2a_purchase = merchant_commerce_service.process_ai_to_ai_purchase(
        buyer_agent_id="AGENT-PROCURE-BOT-42",
        spending_token_limit_inr=100000.0,
        requested_items=[
            {"product_id": "PROD-API-01", "quantity": 5}
        ],
        negotiation_requested=True
    )
    assert a2a_purchase["success"] is True
    assert a2a_purchase["negotiation_summary"]["negotiation_applied"] is True
    assert a2a_purchase["negotiation_summary"]["discount_percentage"] == 12.0  # 5 units = 12% bulk discount
    assert a2a_purchase["safety_and_governance"]["within_spending_bound"] is True
    assert a2a_purchase["payment_execution"]["status"] in ["PAYMENT_LINK_ACTIVE", "SIMULATION_ORDER_CREATED"]
    print(f"AI-to-AI Autonomous Purchase: Total=₹{a2a_purchase['financial_breakdown']['total_payable']:,.2f} (Discount: {a2a_purchase['negotiation_summary']['discount_percentage']}%) [✓ PASSED]")

    # --- 5. Autonomous Marketing Growth Campaign Orchestrator ---
    print("\n--- 5. Testing Autonomous Growth Campaign Orchestrator ---")
    initial_mkt_budget = budget_service.get_department_budget("Marketing")["available_balance"]
    campaign_res = merchant_commerce_service.create_growth_campaign(
        campaign_name="Diwali AI Infrastructure Surge",
        target_audience="Fintech & SaaS CTOs",
        discount_pct=15.0,
        allocated_marketing_budget=50000.0,
        product_ids=["PROD-API-01", "PROD-LLM-03"]
    )
    assert campaign_res["success"] is True
    assert campaign_res["campaign"]["discount_pct"] == 15.0
    assert campaign_res["campaign"]["incremental_revenue_projected"] >= 150000.0
    updated_mkt_budget = budget_service.get_department_budget("Marketing")["available_balance"]
    assert updated_mkt_budget < initial_mkt_budget, "Marketing budget must be deducted for campaign"
    print(f"Campaign Launched: '{campaign_res['campaign']['name']}', ROAS={campaign_res['campaign']['projected_roas']}, Rev Proj=₹{campaign_res['campaign']['incremental_revenue_projected']:,.2f} [✓ PASSED]")

    # --- 6. Explicit Failure Handling & Resilience Modes ---
    print("\n--- 6. Testing Failure Modes & Graceful Recovery ---")
    
    # 6A. API Gateway Drop & Timeout
    fail_gateway = merchant_commerce_service.simulate_failure_mode("API_GATEWAY_TIMEOUT")
    assert fail_gateway["graceful_recovery"] is True
    assert fail_gateway["final_status"] == "RECOVERED_SUCCESSFULLY"
    assert len(fail_gateway["recovery_steps"]) == 4
    print(f"Failure Mode 1 (Gateway Timeout): {fail_gateway['recovery_strategy']} [✓ PASSED]")

    # 6B. Invalid / Malformed Payload
    fail_payload = merchant_commerce_service.simulate_failure_mode("INVALID_PAYLOAD", {"buyer_agent_id": ""})
    assert fail_payload["graceful_recovery"] is True
    assert fail_payload["final_status"] == "REJECTED_WITH_DIAGNOSTICS"
    assert len(fail_payload["validation_errors"]) > 0
    print(f"Failure Mode 2 (Invalid Payload): Safe Rejection with {len(fail_payload['validation_errors'])} diagnostic hints [✓ PASSED]")

    # 6C. Budget Cap Breach
    fail_budget = merchant_commerce_service.simulate_failure_mode("BUDGET_CAP_BREACH", {"department": "Engineering", "amount": 99999999.0})
    assert fail_budget["graceful_recovery"] is True
    assert fail_budget["final_status"] == "SAFE_ABORT_AND_ESCALATED"
    assert "hitl_escalation_ticket" in fail_budget
    print(f"Failure Mode 3 (Budget Cap Hit): Deficit Prevented & Ticket '{fail_budget['hitl_escalation_ticket']}' [✓ PASSED]")

    # 6D. Spending Token Overage
    fail_token = merchant_commerce_service.simulate_failure_mode("TOKEN_SPENDING_OVERAGE", {"buyer_agent_id": "TEST-BOT", "amount": 80000.0, "token_limit": 20000.0})
    assert fail_token["graceful_recovery"] is True
    assert fail_token["final_status"] == "TRANSACTION_PAUSED_FOR_HUMAN_OVERRIDE"
    assert "human_override_authorization_url" in fail_token
    print(f"Failure Mode 4 (Token Limit Breach): Transaction paused for human authorization [✓ PASSED]")

    print("\n==================================================================")
    print("ALL MERCHANT GROWTH & AI COMMERCE TESTS PASSED WITH 100% SUCCESS! ")
    print("==================================================================")


if __name__ == "__main__":
    run_commerce_tests()
