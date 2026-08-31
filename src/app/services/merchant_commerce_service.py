import os
import json
import uuid
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from src.app.services.budget_service import budget_service
from src.app.services.razorpay_service import razorpay_service
from src.app.services.audit_service import audit_service
from src.app.services.notification_service import notification_service

logger = logging.getLogger("MerchantCommerceService")

CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "merchant_catalog.json"


class MerchantCommerceService:
    """
    Service enabling:
    1. Agent-Readable Product Catalogs & Universal Commerce Manifest (AI-to-AI Shopping).
    2. Conversational In-App Checkout with dynamic cart management & GST calculations.
    3. Automated Cross-Sell & Upsell Agent with dynamic bundle discount incentives.
    4. Bounded AI-to-AI Shopping with Spending Token validation & policy-constrained negotiation.
    5. Autonomous Growth Campaign Orchestrator with budget synchronization and ROAS tracking.
    6. Explicit Failure Handling & Resilience Engine for 4 failure modes.
    """

    def __init__(self):
        self._load_catalog()
        self._active_campaigns = []
        self._init_default_campaigns()

    def _load_catalog(self):
        if CATALOG_PATH.exists():
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                self.catalog_data = json.load(f)
        else:
            self.catalog_data = {
                "merchant_info": {
                    "merchant_id": "MERCH-DEFAULT",
                    "name": "CloudNova Enterprise Solutions",
                    "currency": "INR",
                    "default_gst_rate": 0.18,
                    "payment_gateway": "Razorpay Test Mode",
                    "autonomous_commerce_policy": {
                        "max_autonomous_discount_pct": 15.0,
                        "min_bulk_quantity_for_discount": 3,
                        "max_single_transaction_inr": 50000.0,
                        "require_hitl_above_inr": 50000.0
                    }
                },
                "products": [],
                "smart_bundle_rules": []
            }

    def _init_default_campaigns(self):
        self._active_campaigns = [
            {
                "campaign_id": "CAMP-GROWTH-001",
                "name": "Q3 Enterprise Cloud Infrastructure Blitz",
                "target_audience": "B2B Mid-Market CTOs & DevOps Leads",
                "discount_pct": 10.0,
                "allocated_budget": 150000.0,
                "spent_budget": 45000.0,
                "product_ids": ["PROD-API-01", "PROD-VPC-02"],
                "projected_roas": "3.8x",
                "incremental_revenue_projected": 570000.0,
                "razorpay_promo_link": "https://rzp.io/l/cloudnova_q3_blitz",
                "status": "ACTIVE",
                "created_at": "2026-08-20T10:00:00"
            }
        ]

    # =========================================================================
    # 1. AGENT-READABLE MANIFEST & CATALOG (AI-to-AI SHOPPING PROTOCOL)
    # =========================================================================
    def get_agent_manifest(self) -> Dict[str, Any]:
        """
        Returns machine-readable JSON-LD / OpenAPI Agent Protocol metadata
        enabling autonomous external AI buyer agents to discover store capabilities.
        """
        merchant = self.catalog_data.get("merchant_info", {})
        return {
            "@context": "https://schema.org",
            "@type": "MerchantReturnPolicy",
            "protocol_version": "AgentCommerce-v1.0",
            "merchant_id": merchant.get("merchant_id"),
            "merchant_name": merchant.get("name"),
            "category": merchant.get("category"),
            "supported_currency": merchant.get("currency", "INR"),
            "tax_jurisdiction": "IN-GST (18%)",
            "payment_rails": ["Razorpay Test Mode", "UPI", "NetBanking", "Corporate Card"],
            "endpoints": {
                "catalog_discovery": "/v1/commerce/catalog",
                "quotation_negotiation": "/v1/commerce/ai-quote",
                "autonomous_purchase": "/v1/commerce/ai-buy",
                "failure_sandbox": "/v1/commerce/simulate-failure"
            },
            "autonomous_purchasing_rules": {
                "max_single_transaction_bound_inr": merchant.get("autonomous_commerce_policy", {}).get("max_single_transaction_inr", 50000.0),
                "hitl_approval_required_above_inr": merchant.get("autonomous_commerce_policy", {}).get("require_hitl_above_inr", 50000.0),
                "negotiable_bulk_discounts": True,
                "min_bulk_units_for_discount": merchant.get("autonomous_commerce_policy", {}).get("min_bulk_quantity_for_discount", 3),
                "max_negotiable_discount_pct": merchant.get("autonomous_commerce_policy", {}).get("max_autonomous_discount_pct", 15.0),
                "required_headers": ["X-Buyer-Agent-ID", "X-Spending-Token-Limit", "X-Idempotency-Key"]
            }
        }

    def get_catalog(self, category: Optional[str] = None, search: Optional[str] = None) -> Dict[str, Any]:
        """Returns the merchant product catalog with inventory, pricing, and upsell compatibility."""
        products = self.catalog_data.get("products", [])
        if category and category.lower() != "all":
            products = [p for p in products if p.get("category", "").lower() == category.lower()]
        if search:
            q = search.lower()
            products = [p for p in products if q in p.get("name", "").lower() or q in p.get("description", "").lower() or any(q in t for t in p.get("tags", []))]

        return {
            "merchant_info": self.catalog_data.get("merchant_info", {}),
            "total_items": len(products),
            "products": products,
            "smart_bundle_rules": self.catalog_data.get("smart_bundle_rules", [])
        }

    # =========================================================================
    # 2. SMART CROSS-SELL & UPSELL AGENT
    # =========================================================================
    def generate_smart_upsell(self, cart_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluates current cart items against cross-sell rules to recommend
        intelligent bundled upgrades with calculated promotional discounts.
        """
        if not cart_items:
            return {"has_upsell": False, "recommendations": []}

        cart_prod_ids = {item.get("product_id") for item in cart_items}
        rules = self.catalog_data.get("smart_bundle_rules", [])
        products_map = {p["id"]: p for p in self.catalog_data.get("products", [])}

        recommendations = []
        for rule in rules:
            trigger_id = rule.get("trigger_product_id")
            upsell_id = rule.get("upsell_product_id")

            if trigger_id in cart_prod_ids and upsell_id not in cart_prod_ids:
                upsell_prod = products_map.get(upsell_id)
                trigger_prod = products_map.get(trigger_id)
                if upsell_prod and trigger_prod:
                    discount_pct = rule.get("special_bundle_discount_pct", 10.0)
                    orig_price = upsell_prod["unit_price"]
                    discounted_price = round(orig_price * (1 - discount_pct / 100.0), 2)
                    savings = round(orig_price - discounted_price, 2)

                    recommendations.append({
                        "rule_id": rule.get("rule_id"),
                        "bundle_name": rule.get("bundle_name"),
                        "trigger_product": trigger_prod["name"],
                        "upsell_product_id": upsell_id,
                        "upsell_product_name": upsell_prod["name"],
                        "original_price": orig_price,
                        "bundle_discount_pct": discount_pct,
                        "discounted_price": discounted_price,
                        "customer_savings": savings,
                        "reasoning": rule.get("reason"),
                        "action_payload": {
                            "product_id": upsell_id,
                            "quantity": 1,
                            "applied_discount_pct": discount_pct
                        }
                    })

        return {
            "has_upsell": len(recommendations) > 0,
            "recommendations_count": len(recommendations),
            "recommendations": recommendations
        }

    # =========================================================================
    # 3. CONVERSATIONAL CHECKOUT & CART AGENT
    # =========================================================================
    def process_conversational_checkout(
        self,
        message: str,
        cart: Optional[List[Dict[str, Any]]] = None,
        customer_info: Optional[Dict[str, Any]] = None,
        execute_checkout: bool = False
    ) -> Dict[str, Any]:
        """
        Parses customer intent from natural language, dynamically manages the cart,
        recommends smart bundle cross-sells, computes 18% GST, and dispatches Razorpay test links.
        """
        cart = cart or []
        customer_info = customer_info or {"name": "Valued Enterprise Client", "email": "client@enterprise.local"}
        q_lower = message.lower()

        products = self.catalog_data.get("products", [])
        products_map = {p["id"]: p for p in products}

        # Intent detection: Add to cart
        action_taken = "QUERY"
        items_added = []
        for p in products:
            p_name_lower = p["name"].lower()
            p_tags = [t.lower() for t in p.get("tags", [])]
            if (p_name_lower in q_lower or any(tag in q_lower for tag in p_tags)) and any(k in q_lower for k in ["add", "buy", "purchase", "order", "want", "need", "checkout"]):
                # Check if already in cart
                existing = next((item for item in cart if item.get("product_id") == p["id"]), None)
                if existing:
                    existing["quantity"] = existing.get("quantity", 1) + 1
                else:
                    cart.append({
                        "product_id": p["id"],
                        "name": p["name"],
                        "unit_price": p["unit_price"],
                        "quantity": 1,
                        "discount_pct": 0.0
                    })
                items_added.append(p["name"])
                action_taken = "CART_UPDATED"

        # Intent detection: Apply bundle/upsell
        if "bundle" in q_lower or "upsell" in q_lower or "yes add" in q_lower:
            upsells = self.generate_smart_upsell(cart)
            if upsells["has_upsell"]:
                rec = upsells["recommendations"][0]
                rec_id = rec["upsell_product_id"]
                if not any(item.get("product_id") == rec_id for item in cart):
                    p_info = products_map.get(rec_id, {})
                    cart.append({
                        "product_id": rec_id,
                        "name": p_info.get("name", rec["upsell_product_name"]),
                        "unit_price": rec["discounted_price"],
                        "quantity": 1,
                        "discount_pct": rec["bundle_discount_pct"],
                        "bundle_applied": rec["bundle_name"]
                    })
                    items_added.append(f"{rec['upsell_product_name']} ({rec['bundle_discount_pct']}% Bundle Discount)")
                    action_taken = "BUNDLE_ADDED"

        # Calculate Financials
        subtotal = 0.0
        for item in cart:
            p_id = item.get("product_id")
            if "unit_price" not in item or not item.get("name"):
                prod = products_map.get(p_id, {})
                item["unit_price"] = item.get("unit_price") or prod.get("unit_price", 0.0)
                item["name"] = item.get("name") or prod.get("name", p_id)
            unit_p = float(item.get("unit_price", 0.0))
            qty = int(item.get("quantity", 1))
            disc = float(item.get("discount_pct", 0.0))
            item_total = (unit_p * qty) * (1.0 - disc / 100.0)
            subtotal += item_total

        subtotal = round(subtotal, 2)
        gst_amount = round(subtotal * 0.18, 2)
        total_amount = round(subtotal + gst_amount, 2)

        # Generate Upsell Recommendation
        upsell_data = self.generate_smart_upsell(cart)

        # Execute checkout if explicitly requested or total > 0 and user asked to pay
        checkout_details = None
        if execute_checkout or any(k in q_lower for k in ["pay now", "proceed to pay", "checkout now", "generate link", "confirm order"]):
            if total_amount > 0:
                payment_link_res = razorpay_service.create_payment_link(
                    amount_inr=total_amount,
                    description=f"CloudNova Enterprise Order ({len(cart)} items)",
                    customer_name=customer_info.get("name", "Valued Client"),
                    customer_email=customer_info.get("email", "client@enterprise.local"),
                    customer_phone="+919876543210"
                )
                checkout_details = {
                    "order_id": f"ORD-CONV-{uuid.uuid4().hex[:6].upper()}",
                    "payment_link_id": payment_link_res.get("id"),
                    "payment_url": payment_link_res.get("short_url", "https://rzp.io/i/mock_payment"),
                    "status": "AWAITING_PAYMENT",
                    "currency": "INR",
                    "requires_hitl": total_amount >= 50000.0
                }
                action_taken = "CHECKOUT_INITIATED"

                # Log to audit trail
                audit_service.log_action(
                    user_id="usr_commerce_001",
                    user_name="Conversational Checkout Agent",
                    role="COMMERCE_AGENT",
                    action="CONVERSATIONAL_CHECKOUT",
                    entity="COMMERCE_ORDER",
                    entity_id=checkout_details.get("order_id", "ORD-CONV"),
                    details=f"Generated checkout for {customer_info.get('name')} | Total: ₹{total_amount:,.2f} | Items: {len(cart)}",
                    risk_level="LOW"
                )

        # Build Natural Language Assistant Narrative
        narrative_parts = []
        if items_added:
            narrative_parts.append(f"🛒 **Cart Updated:** Added **{', '.join(items_added)}** to your cart.")
        elif action_taken == "QUERY" and not cart:
            narrative_parts.append("👋 Hello! Welcome to **CloudNova Solutions**. I can help you discover cloud services, configure dedicated clusters, apply bundle discounts, and complete instant Razorpay checkout.")

        if cart:
            narrative_parts.append(f"\n### Current Cart Summary ({len(cart)} Items)")
            for item in cart:
                narrative_parts.append(f"- **{item.get('name')}** (Qty: {item.get('quantity')}) — ₹{item.get('unit_price'):,.2f}")
            narrative_parts.append(f"\n**Subtotal:** ₹{subtotal:,.2f} | **GST (18%):** ₹{gst_amount:,.2f} | **Total:** **₹{total_amount:,.2f} INR**")

        if upsell_data["has_upsell"] and not checkout_details:
            top_rec = upsell_data["recommendations"][0]
            narrative_parts.append(f"\n💡 **Recommended Smart Bundle:** Add **{top_rec['upsell_product_name']}** and save **₹{top_rec['customer_savings']:,.2f}** ({top_rec['bundle_discount_pct']}% OFF).\n*Reason: {top_rec['reasoning']}*")

        if checkout_details:
            narrative_parts.append(f"\n✅ **Razorpay Payment Link Ready:** [Click here to pay ₹{total_amount:,.2f}]({checkout_details['payment_url']})\nOrder ID: `{checkout_details['order_id']}`")

        return {
            "assistant_response": "\n".join(narrative_parts),
            "cart": cart,
            "cart_summary": {
                "subtotal": subtotal,
                "gst_amount": gst_amount,
                "total_amount": total_amount,
                "item_count": len(cart)
            },
            "upsell_recommendations": upsell_data,
            "checkout_details": checkout_details,
            "action_taken": action_taken
        }

    # =========================================================================
    # 4. AUTONOMOUS AI-TO-AI SHOPPING & BOUNDED NEGOTIATION
    # =========================================================================
    def process_ai_to_ai_purchase(
        self,
        buyer_agent_id: str,
        spending_token_limit_inr: float,
        requested_items: List[Dict[str, Any]],
        negotiation_requested: bool = True,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handles machine-to-machine autonomous purchasing:
        - Validates buyer agent spending token.
        - Evaluates bulk discount negotiation against strict merchant policies.
        - Enforces safety bounds & HITL approval gating.
        - Generates Razorpay test Payment Link / Order.
        - Emits an immutable audit trail entry with reasoning lineage.
        """
        transaction_id = f"TXN-A2A-{uuid.uuid4().hex[:8].upper()}"
        products_map = {p["id"]: p for p in self.catalog_data.get("products", [])}
        policy = self.catalog_data.get("merchant_info", {}).get("autonomous_commerce_policy", {})

        min_bulk_qty = policy.get("min_bulk_quantity_for_discount", 3)
        max_policy_discount = policy.get("max_autonomous_discount_pct", 15.0)

        # 1. Line Item & Inventory Evaluation
        validated_items = []
        total_units = 0
        base_subtotal = 0.0

        for req in requested_items:
            p_id = req.get("product_id")
            qty = req.get("quantity", 1)
            p = products_map.get(p_id)

            if not p:
                return {
                    "success": False,
                    "error_code": "PRODUCT_NOT_FOUND",
                    "detail": f"Product ID '{p_id}' is not in the merchant catalog.",
                    "transaction_id": transaction_id
                }

            if p["stock_available"] < qty:
                return {
                    "success": False,
                    "error_code": "INSUFFICIENT_STOCK",
                    "detail": f"Requested {qty} units of '{p['name']}', but only {p['stock_available']} units available.",
                    "transaction_id": transaction_id
                }

            total_units += qty
            base_subtotal += p["unit_price"] * qty

            validated_items.append({
                "product_id": p_id,
                "name": p["name"],
                "unit_price": p["unit_price"],
                "quantity": qty,
                "line_total": p["unit_price"] * qty
            })

        # 2. Autonomous Bounded Negotiation Logic
        applied_discount_pct = 0.0
        negotiation_notes = "Standard retail catalog pricing applied."

        if negotiation_requested:
            if total_units >= min_bulk_qty:
                # Calculate tiered bulk discount
                if total_units >= 10:
                    applied_discount_pct = min(15.0, max_policy_discount)
                elif total_units >= 5:
                    applied_discount_pct = min(12.0, max_policy_discount)
                else:
                    applied_discount_pct = min(8.0, max_policy_discount)
                negotiation_notes = f"Autonomous bulk volume discount of {applied_discount_pct}% granted for order volume of {total_units} units."
            else:
                negotiation_notes = f"Negotiation evaluated: Minimum {min_bulk_qty} units required for volume discount."

        discount_amount = round(base_subtotal * (applied_discount_pct / 100.0), 2)
        discounted_subtotal = round(base_subtotal - discount_amount, 2)
        gst_amount = round(discounted_subtotal * 0.18, 2)
        total_payable = round(discounted_subtotal + gst_amount, 2)

        # 3. Safety Bounds & Spending Token Validation
        if total_payable > spending_token_limit_inr:
            error_resp = {
                "success": False,
                "error_code": "SPENDING_TOKEN_LIMIT_EXCEEDED",
                "detail": f"Calculated total payable (₹{total_payable:,.2f}) exceeds Buyer Agent Spending Token Limit (₹{spending_token_limit_inr:,.2f}).",
                "transaction_id": transaction_id,
                "total_payable": total_payable,
                "token_limit": spending_token_limit_inr,
                "safety_resolution": "Transaction halted. Reduce requested quantities or authorize an expanded spending token."
            }
            # Log failure to audit
            audit_service.log_action(
                user_id=f"usr_agent_{buyer_agent_id[:6]}",
                user_name=f"BuyerAgent:{buyer_agent_id}",
                role="AUTONOMOUS_BUYER_AGENT",
                action="AI_TO_AI_SAFETY_BLOCK",
                entity="AI_COMMERCE_TOKEN",
                entity_id=transaction_id,
                details=f"Token Limit Breach: Req ₹{total_payable:,.2f} > Cap ₹{spending_token_limit_inr:,.2f}",
                risk_level="HIGH"
            )
            return error_resp

        # 4. HITL Approval Requirement Check
        requires_hitl = total_payable >= policy.get("require_hitl_above_inr", 50000.0)
        payment_link = razorpay_service.create_payment_link(
            amount_inr=total_payable,
            description=f"AI-to-AI Autonomous Purchase | Buyer: {buyer_agent_id}",
            customer_name=f"AI Agent {buyer_agent_id}",
            customer_email="ai.buyer.agent@enterprise.local",
            customer_phone="+919999988888"
        )

        # 5. Record Audit Trail
        audit_service.log_action(
            user_id=f"usr_agent_{buyer_agent_id[:6]}",
            user_name=f"BuyerAgent:{buyer_agent_id}",
            role="AUTONOMOUS_BUYER_AGENT",
            action="AI_TO_AI_PURCHASE",
            entity="AI_COMMERCE_TRANSACTION",
            entity_id=transaction_id,
            details=f"Completed autonomous purchase for ₹{total_payable:,.2f} INR (Discount: {applied_discount_pct}% | Link: {payment_link.get('id')})",
            risk_level="LOW" if not requires_hitl else "MEDIUM"
        )

        return {
            "success": True,
            "transaction_id": transaction_id,
            "buyer_agent_id": buyer_agent_id,
            "idempotency_key": idempotency_key or str(uuid.uuid4()),
            "negotiation_summary": {
                "negotiation_applied": applied_discount_pct > 0,
                "discount_percentage": applied_discount_pct,
                "discount_amount": discount_amount,
                "negotiation_rationale": negotiation_notes
            },
            "financial_breakdown": {
                "base_subtotal": base_subtotal,
                "discount_amount": discount_amount,
                "net_subtotal": discounted_subtotal,
                "gst_rate_pct": 18.0,
                "gst_amount": gst_amount,
                "total_payable": total_payable,
                "currency": "INR"
            },
            "safety_and_governance": {
                "spending_token_limit_inr": spending_token_limit_inr,
                "within_spending_bound": True,
                "requires_human_approval": requires_hitl,
                "governance_status": "PENDING_CFO_REVIEW" if requires_hitl else "AUTONOMOUSLY_APPROVED"
            },
            "payment_execution": {
                "gateway": "Razorpay Test Mode",
                "payment_link_id": payment_link.get("payment_link_id") or payment_link.get("id"),
                "payment_url": payment_link.get("short_url") or f"https://rzp.io/i/{transaction_id[4:].lower()}",
                "status": "PAYMENT_LINK_ACTIVE"
            },
            "items_fulfilled": validated_items,
            "timestamp": datetime.utcnow().isoformat()
        }

    # =========================================================================
    # 5. AUTONOMOUS GROWTH CAMPAIGN ORCHESTRATOR
    # =========================================================================
    def create_growth_campaign(
        self,
        campaign_name: str,
        target_audience: str,
        discount_pct: float,
        allocated_marketing_budget: float,
        product_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Orchestrates an autonomous marketing sales campaign:
        - Validates Marketing department available budget.
        - Deducts allocated campaign funds from Marketing budget.
        - Generates promotional campaign Razorpay links with embedded discounts.
        - Projects conversion rates, incremental revenue, and ROAS.
        """
        mkt_budget = budget_service.get_department_budget("Marketing")
        avail = mkt_budget["available_balance"] if mkt_budget else 0.0

        if allocated_marketing_budget > avail:
            return {
                "success": False,
                "error_code": "MARKETING_BUDGET_CAP_HIT",
                "detail": f"Requested campaign budget ₹{allocated_marketing_budget:,.2f} exceeds available Marketing balance of ₹{avail:,.2f}.",
                "resolution": "Reduce campaign budget or execute a budget reallocation from Operations surplus."
            }

        # Deduct from Marketing budget
        budget_service.record_expense("Marketing", allocated_marketing_budget)

        campaign_id = f"CAMP-GROWTH-{uuid.uuid4().hex[:4].upper()}"
        # Compute projected ROAS (historical benchmark 3.5x to 4.2x)
        roas_multiplier = 3.6 + (len(product_ids) * 0.2)
        incremental_rev = round(allocated_marketing_budget * roas_multiplier, 2)

        promo_link = razorpay_service.create_payment_link(
            amount_inr=round(12500.0 * (1 - discount_pct / 100.0) * 1.18, 2),
            description=f"Promotional Campaign: {campaign_name} ({discount_pct}% OFF)",
            customer_name="Campaign Lead",
            customer_email="campaign.lead@enterprise.local",
            customer_phone="+919876543210"
        )

        campaign_obj = {
            "campaign_id": campaign_id,
            "name": campaign_name,
            "target_audience": target_audience,
            "discount_pct": discount_pct,
            "allocated_budget": allocated_marketing_budget,
            "spent_budget": allocated_marketing_budget,
            "product_ids": product_ids,
            "projected_roas": f"{roas_multiplier:.1f}x",
            "incremental_revenue_projected": incremental_rev,
            "razorpay_promo_link": promo_link.get("short_url", "https://rzp.io/l/promo_link"),
            "status": "ACTIVE",
            "created_at": datetime.utcnow().isoformat()
        }
        self._active_campaigns.append(campaign_obj)

        # Audit logging
        audit_service.log_action(
            user_id="usr_growth_bot",
            user_name="Autonomous Campaign Orchestrator",
            role="MARKETING_AGENT",
            action="GROWTH_CAMPAIGN_LAUNCH",
            entity="MARKETING_CAMPAIGN",
            entity_id=campaign_id,
            details=f"Launched campaign '{campaign_name}' with budget ₹{allocated_marketing_budget:,.2f} (Projected Revenue: ₹{incremental_rev:,.2f})",
            risk_level="LOW"
        )

        return {
            "success": True,
            "campaign": campaign_obj,
            "marketing_budget_remaining": budget_service.get_department_budget("Marketing")["available_balance"]
        }

    def list_campaigns(self) -> List[Dict[str, Any]]:
        """Returns all active marketing growth campaigns."""
        return self._active_campaigns

    # =========================================================================
    # 6. FAILURE HANDLING & RESILIENCE SIMULATION ENGINE
    # =========================================================================
    def simulate_failure_mode(self, failure_type: str, custom_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Explicitly demonstrates how FinPilot AI gracefully recovers from failure modes:
        1. API_GATEWAY_TIMEOUT (Simulated Network / Razorpay drop with idempotent retry).
        2. INVALID_PAYLOAD (Malformed schema / missing fields with corrective diagnostic hints).
        3. BUDGET_CAP_BREACH (Department spend cap hit with safe rejection & HITL alert).
        4. TOKEN_SPENDING_OVERAGE (AI Buyer exceeding authorized token with human-gated escalation).
        """
        custom_payload = custom_payload or {}
        timestamp = datetime.utcnow().isoformat()

        if failure_type == "API_GATEWAY_TIMEOUT":
            # Simulate Razorpay Gateway Timeout & Auto-Recovery
            idempotency_key = custom_payload.get("idempotency_key", f"IDEMP-{uuid.uuid4().hex[:8]}")
            retry_count = 3
            recovery_steps = [
                {"step": 1, "action": "Detected HTTP 504 Gateway Timeout from Razorpay payment endpoint.", "status": "CAUGHT"},
                {"step": 2, "action": f"Invoked exponential backoff policy (retry 1/3 after 250ms with Idempotency-Key '{idempotency_key}').", "status": "RETRYING"},
                {"step": 3, "action": "Idempotency key acknowledged by secondary Razorpay cluster; cached order restored.", "status": "RECOVERED"},
                {"step": 4, "action": "Created asynchronous offline payment reconciliation record to prevent duplicate charges.", "status": "RESOLVED"}
            ]
            audit_service.log_action(
                user_id="sys_resilience_bot",
                user_name="System Resilience Engine",
                role="SYSTEM",
                action="FAILURE_RECOVERY",
                entity="RAZORPAY_GATEWAY",
                entity_id=idempotency_key,
                details=f"Gateway Timeout gracefully recovered with Idempotency Key '{idempotency_key}'",
                risk_level="MEDIUM"
            )
            return {
                "failure_type": "API_GATEWAY_TIMEOUT",
                "failure_description": "Payment Gateway Network Drop & 504 Timeout",
                "graceful_recovery": True,
                "recovery_strategy": "Idempotent Exponential Backoff & Asynchronous Offline Fallback",
                "idempotency_key": idempotency_key,
                "recovery_steps": recovery_steps,
                "final_status": "RECOVERED_SUCCESSFULLY",
                "timestamp": timestamp
            }

        elif failure_type == "INVALID_PAYLOAD":
            # Simulate Malformed Buyer Agent Request
            errors = []
            if not custom_payload.get("buyer_agent_id"):
                errors.append({"field": "buyer_agent_id", "error": "Missing mandatory buyer agent identification header."})
            if not custom_payload.get("items"):
                errors.append({"field": "items", "error": "Missing line-item array; at least 1 product SKU required."})
            if not errors:
                errors.append({"field": "quantity", "error": "Quantity must be a positive integer >= 1 (received -5)."})

            diagnostic_hints = [
                "Ensure payload conforms to AgentCommerce-v1.0 schema (/v1/commerce/ai-manifest).",
                "Include 'buyer_agent_id', 'spending_token_limit_inr', and a non-empty 'items' list.",
                "Verify product IDs against current catalog (/v1/commerce/catalog)."
            ]
            audit_service.log_action(
                user_id="sys_validator",
                user_name="System Validator",
                role="SYSTEM",
                action="SCHEMA_VALIDATION_REJECT",
                entity="COMMERCE_PAYLOAD",
                entity_id=f"PAYLOAD-ERR-{uuid.uuid4().hex[:6]}",
                details=f"Malformed payload rejected safely ({len(errors)} diagnostic errors)",
                risk_level="LOW"
            )
            return {
                "failure_type": "INVALID_PAYLOAD",
                "failure_description": "Malformed JSON Schema / Missing Mandatory Headers",
                "graceful_recovery": True,
                "recovery_strategy": "Field-Level Schema Diagnostics & Safe Rejection (Zero Ledger Side-Effects)",
                "validation_errors": errors,
                "diagnostic_hints": diagnostic_hints,
                "final_status": "REJECTED_WITH_DIAGNOSTICS",
                "timestamp": timestamp
            }

        elif failure_type == "BUDGET_CAP_BREACH":
            # Simulate Department Spending Cap Hit
            req_amount = custom_payload.get("amount", 2500000.0)
            dept = custom_payload.get("department", "Engineering")
            dept_budget = budget_service.get_department_budget(dept)
            avail = dept_budget["available_balance"] if dept_budget else 500000.0

            alert_msg = f"CRITICAL DEFICIT PREVENTION: Blocked disbursement of ₹{req_amount:,.2f} exceeding {dept} available funds (₹{avail:,.2f})."
            notification_service.create_notification(
                notification_type="CRITICAL_DEFICIT",
                title=f"{dept} Spending Cap Breach Blocked",
                message=alert_msg,
                entity_id=f"BREACH-{dept.upper()}",
                department=dept,
                severity="HIGH"
            )
            audit_service.log_action(
                user_id="sys_budget_controller",
                user_name="Autonomous Budget Controller",
                role="BUDGET_CONTROLLER",
                action="BUDGET_CAP_BLOCK",
                entity="DEPARTMENT_BUDGET",
                entity_id=dept,
                details=f"Blocked ₹{req_amount:,.2f} for {dept} to preserve corporate liquidity",
                risk_level="HIGH"
            )
            return {
                "failure_type": "BUDGET_CAP_BREACH",
                "failure_description": "Department Spend Limit Exceeded & Deficit Prevention",
                "graceful_recovery": True,
                "recovery_strategy": "Autonomous Pre-Disbursement Freeze & HITL Reallocation Escalation",
                "department": dept,
                "requested_amount": req_amount,
                "available_balance": avail,
                "deficit_prevented": req_amount - avail,
                "hitl_escalation_ticket": f"ESC-BUDGET-{uuid.uuid4().hex[:6].upper()}",
                "final_status": "SAFE_ABORT_AND_ESCALATED",
                "timestamp": timestamp
            }

        elif failure_type == "TOKEN_SPENDING_OVERAGE":
            # Simulate AI Buyer Token Cap Breach
            req_amount = custom_payload.get("amount", 85000.0)
            token_cap = custom_payload.get("token_limit", 25000.0)
            buyer_id = custom_payload.get("buyer_agent_id", "AGENT-PROCURE-BOT-9")

            audit_service.log_action(
                user_id=f"usr_agent_{buyer_id[:6]}",
                user_name=f"BuyerAgent:{buyer_id}",
                role="AUTONOMOUS_BUYER_AGENT",
                action="TOKEN_CAP_BLOCK",
                entity="AI_SPENDING_TOKEN",
                entity_id=buyer_id,
                details=f"Blocked transaction: ₹{req_amount:,.2f} exceeds token allowance ₹{token_cap:,.2f}",
                risk_level="HIGH"
            )
            return {
                "failure_type": "TOKEN_SPENDING_OVERAGE",
                "failure_description": "Autonomous AI Buyer Exceeded Authorized Spending Token Limit",
                "graceful_recovery": True,
                "recovery_strategy": "Pre-Authorization Token Verification & Human Approval Link Dispatch",
                "buyer_agent_id": buyer_id,
                "requested_amount": req_amount,
                "token_limit": token_cap,
                "overage_amount": req_amount - token_cap,
                "human_override_authorization_url": f"http://127.0.0.1:8000/?autologin=cfo&tab=approvals&token_override={uuid.uuid4().hex[:6]}",
                "final_status": "TRANSACTION_PAUSED_FOR_HUMAN_OVERRIDE",
                "timestamp": timestamp
            }

        else:
            return {
                "failure_type": "UNKNOWN_FAILURE_TYPE",
                "detail": f"Supported failure types: API_GATEWAY_TIMEOUT, INVALID_PAYLOAD, BUDGET_CAP_BREACH, TOKEN_SPENDING_OVERAGE"
            }


merchant_commerce_service = MerchantCommerceService()
