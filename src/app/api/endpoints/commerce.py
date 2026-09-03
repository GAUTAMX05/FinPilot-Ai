# -*- coding: utf-8 -*-
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends, Header, Response

from src.app.core.rate_limiter import rate_limiter
from src.app.core.validators import validate_monetary_amount, validate_percentage, sanitize_text
from src.app.services.idempotency_service import idempotency_service
from src.app.services.merchant_commerce_service import merchant_commerce_service

router = APIRouter(prefix="/commerce", tags=["Merchant Sales Growth & AI-to-AI Shopping"])


class ConversationalCheckoutRequest(BaseModel):
    message: str = Field(..., max_length=1000, description="Customer natural language message or query.")
    cart: Optional[List[Dict[str, Any]]] = Field(default=[], description="Current shopping cart items.")
    customer_info: Optional[Dict[str, Any]] = Field(default=None, description="Customer contact info.")
    execute_checkout: Optional[bool] = Field(default=False, description="Whether to trigger Razorpay checkout link generation immediately.")


class AIBuyerItem(BaseModel):
    product_id: str = Field(..., max_length=50, description="Target Product ID from merchant catalog.")
    quantity: int = Field(default=1, ge=1, le=1000, description="Quantity to purchase.")


class AIQuoteRequest(BaseModel):
    buyer_agent_id: str = Field(..., max_length=80, description="Autonomous Buyer Agent Identifier.")
    items: List[AIBuyerItem] = Field(..., min_length=1, max_length=50, description="List of items requested.")
    spending_token_limit_inr: float = Field(..., gt=0, le=1_000_000_000.0, description="Spending Token budget ceiling for the transaction.")
    request_volume_discount: Optional[bool] = Field(default=True, description="Whether to negotiate bulk discount.")


class AIBuyRequest(BaseModel):
    buyer_agent_id: str = Field(..., max_length=80, description="Autonomous Buyer Agent Identifier.")
    spending_token_limit_inr: float = Field(..., gt=0, le=1_000_000_000.0, description="Spending Token budget ceiling for the transaction.")
    items: List[AIBuyerItem] = Field(..., min_length=1, max_length=50, description="List of items to purchase.")
    negotiation_requested: Optional[bool] = Field(default=True, description="Whether to negotiate volume discounts.")
    idempotency_key: Optional[str] = Field(default=None, max_length=100, description="Idempotency key to prevent duplicate purchases.")


class GrowthCampaignRequest(BaseModel):
    name: str = Field(..., max_length=100, description="Campaign name.")
    target_audience: str = Field(..., max_length=100, description="Target audience / customer segment.")
    discount_pct: float = Field(..., ge=0, le=50, description="Promotional discount percentage.")
    allocated_marketing_budget: float = Field(..., gt=0, le=100_000_000.0, description="Budget in INR allocated from Marketing department.")
    product_ids: List[str] = Field(..., min_length=1, max_length=20, description="Product IDs featured in campaign.")


class FailureSimulationRequest(BaseModel):
    failure_type: str = Field(..., description="One of: API_GATEWAY_TIMEOUT, INVALID_PAYLOAD, BUDGET_CAP_BREACH, TOKEN_SPENDING_OVERAGE")
    custom_payload: Optional[Dict[str, Any]] = Field(default={}, description="Optional custom parameters for simulation.")


@router.get("/ai-manifest")
def get_ai_manifest():
    """
    Returns the Agent-Readable Universal Commerce Protocol manifest (JSON-LD / OpenAPI).
    Allows external autonomous AI buying agents to discover store endpoints, currency, and policy bounds.
    """
    return merchant_commerce_service.get_agent_manifest()


@router.get("/catalog")
def get_catalog(category: Optional[str] = None, search: Optional[str] = None):
    """
    Returns the merchant's machine-readable product catalog with live inventory,
    pricing, tags, and smart bundle rules.
    """
    clean_cat = sanitize_text(category, field_name="Category", max_length=50) if category else None
    clean_search = sanitize_text(search, field_name="Search Query", max_length=100) if search else None
    return merchant_commerce_service.get_catalog(category=clean_cat, search=clean_search)


@router.post("/conversational-checkout")
def conversational_checkout(req: ConversationalCheckoutRequest):
    """
    Conversational in-app shopping assistant with rate limiting and input sanitization.
    Parses intent, manages cart, calculates 18% GST, injects smart upsell bundles,
    and generates Razorpay payment links.
    """
    rate_limiter.check_rate_limit(client_key="conversational_checkout_user", estimated_tokens=150)
    clean_msg = sanitize_text(req.message, field_name="Message", max_length=1000, allow_empty=False)

    res = merchant_commerce_service.process_conversational_checkout(
        message=clean_msg,
        cart=req.cart or [],
        customer_info=req.customer_info,
        execute_checkout=req.execute_checkout or False
    )
    return res


@router.post("/ai-quote")
def request_ai_quote(req: AIQuoteRequest):
    """
    AI-to-AI quotation and negotiation endpoint with rate limiting.
    Evaluates requested items against merchant volume discount policies and inventory.
    """
    clean_buyer = sanitize_text(req.buyer_agent_id, field_name="Buyer Agent ID", max_length=80, allow_empty=False)
    rate_limiter.check_rate_limit(client_key=clean_buyer, estimated_tokens=100)
    valid_token = validate_monetary_amount(req.spending_token_limit_inr, field_name="Spending Token Limit", min_amount=1.0)

    res = merchant_commerce_service.process_ai_to_ai_purchase(
        buyer_agent_id=clean_buyer,
        spending_token_limit_inr=valid_token,
        requested_items=[item.model_dump() for item in req.items],
        negotiation_requested=req.request_volume_discount or True
    )
    return res


@router.post("/ai-buy")
def execute_ai_buy(
    req: AIBuyRequest,
    response: Response,
    x_buyer_agent_id: Optional[str] = Header(None),
    x_spending_token_limit: Optional[float] = Header(None),
    x_idempotency_key: Optional[str] = Header(None)
):
    """
    Autonomous AI-to-AI purchase execution endpoint with:
    - Server-side X-Idempotency-Key deduplication
    - Rate limiting per Buyer Agent
    - Hard token cap and 15% discount limit gating in deterministic code
    - Immutable SHA-256 audit ledger records
    """
    buyer_id = sanitize_text(x_buyer_agent_id or req.buyer_agent_id, field_name="Buyer Agent ID", max_length=80, allow_empty=False)
    token_limit = validate_monetary_amount(x_spending_token_limit or req.spending_token_limit_inr, field_name="Spending Token Limit", min_amount=1.0)
    idemp_key = sanitize_text(x_idempotency_key or req.idempotency_key, field_name="Idempotency Key", max_length=100) if (x_idempotency_key or req.idempotency_key) else None

    # 1. Check Idempotency Cache
    if idemp_key:
        cached = idempotency_service.get_cached_response(idemp_key)
        if cached:
            response.headers["X-Cache"] = "IDEMPOTENT-HIT"
            return cached

    # 2. Rate Limiting Check
    rate_limiter.check_rate_limit(client_key=buyer_id, estimated_tokens=200)

    # 3. Execute Autonomous Purchase
    res = merchant_commerce_service.process_ai_to_ai_purchase(
        buyer_agent_id=buyer_id,
        spending_token_limit_inr=token_limit,
        requested_items=[item.model_dump() for item in req.items],
        negotiation_requested=req.negotiation_requested or True,
        idempotency_key=idemp_key
    )

    # 4. Record to Idempotency Store
    if idemp_key and res.get("success"):
        idempotency_service.record_response(idemp_key, res)

    return res


@router.post("/campaigns/create")
def create_growth_campaign(req: GrowthCampaignRequest):
    """
    Autonomous Marketing Growth Campaign Orchestrator with validation.
    Deducts allocated funds from Marketing department budget, generates promotional Razorpay links,
    and tracks projected ROAS and incremental sales.
    """
    clean_name = sanitize_text(req.name, field_name="Campaign Name", max_length=100, allow_empty=False)
    clean_aud = sanitize_text(req.target_audience, field_name="Target Audience", max_length=100, allow_empty=False)
    valid_disc = validate_percentage(req.discount_pct, field_name="Discount Percentage", min_pct=0.0, max_pct=50.0)
    valid_budget = validate_monetary_amount(req.allocated_marketing_budget, field_name="Allocated Marketing Budget", min_amount=100.0)

    res = merchant_commerce_service.create_growth_campaign(
        campaign_name=clean_name,
        target_audience=clean_aud,
        discount_pct=valid_disc,
        allocated_marketing_budget=valid_budget,
        product_ids=req.product_ids
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("detail"))
    return res


@router.get("/campaigns")
def list_growth_campaigns():
    """Returns active promotional campaigns and sales performance metrics."""
    return {"campaigns": merchant_commerce_service.list_campaigns()}


@router.post("/simulate-failure")
def simulate_failure(req: FailureSimulationRequest):
    """
    Failure Handling & Resilience Testbed.
    Demonstrates graceful recovery for:
    - API_GATEWAY_TIMEOUT (Idempotent retry with exponential backoff)
    - INVALID_PAYLOAD (Field-level schema diagnostics)
    - BUDGET_CAP_BREACH (Pre-disbursement freeze & HITL alert)
    - TOKEN_SPENDING_OVERAGE (AI buyer token limit breach & human gating)
    """
    clean_type = sanitize_text(req.failure_type, field_name="Failure Type", max_length=50, allow_empty=False)
    return merchant_commerce_service.simulate_failure_mode(
        failure_type=clean_type,
        custom_payload=req.custom_payload or {}
    )
