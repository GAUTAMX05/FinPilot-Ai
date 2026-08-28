from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends, Header
from src.app.services.merchant_commerce_service import merchant_commerce_service
from src.app.core.auth_middleware import get_current_user

router = APIRouter(prefix="/commerce", tags=["Merchant Sales Growth & AI-to-AI Shopping"])


class ConversationalCheckoutRequest(BaseModel):
    message: str = Field(..., description="Customer natural language message or query.")
    cart: Optional[List[Dict[str, Any]]] = Field(default=[], description="Current shopping cart items.")
    customer_info: Optional[Dict[str, Any]] = Field(default=None, description="Customer contact info.")
    execute_checkout: Optional[bool] = Field(default=False, description="Whether to trigger Razorpay checkout link generation immediately.")


class AIBuyerItem(BaseModel):
    product_id: str = Field(..., description="Target Product ID from merchant catalog.")
    quantity: int = Field(default=1, ge=1, description="Quantity to purchase.")


class AIQuoteRequest(BaseModel):
    buyer_agent_id: str = Field(..., description="Autonomous Buyer Agent Identifier.")
    items: List[AIBuyerItem] = Field(..., description="List of items requested.")
    spending_token_limit_inr: float = Field(..., gt=0, description="Spending Token budget ceiling for the transaction.")
    request_volume_discount: Optional[bool] = Field(default=True, description="Whether to negotiate bulk discount.")


class AIBuyRequest(BaseModel):
    buyer_agent_id: str = Field(..., description="Autonomous Buyer Agent Identifier.")
    spending_token_limit_inr: float = Field(..., gt=0, description="Spending Token budget ceiling for the transaction.")
    items: List[AIBuyerItem] = Field(..., description="List of items to purchase.")
    negotiation_requested: Optional[bool] = Field(default=True, description="Whether to negotiate volume discounts.")
    idempotency_key: Optional[str] = Field(default=None, description="Idempotency key to prevent duplicate purchases.")


class GrowthCampaignRequest(BaseModel):
    name: str = Field(..., description="Campaign name.")
    target_audience: str = Field(..., description="Target audience / customer segment.")
    discount_pct: float = Field(..., ge=0, le=50, description="Promotional discount percentage.")
    allocated_marketing_budget: float = Field(..., gt=0, description="Budget in INR allocated from Marketing department.")
    product_ids: List[str] = Field(..., description="Product IDs featured in campaign.")


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
    return merchant_commerce_service.get_catalog(category=category, search=search)


@router.post("/conversational-checkout")
def conversational_checkout(req: ConversationalCheckoutRequest):
    """
    Conversational in-app shopping assistant.
    Parses intent, manages cart, calculates 18% GST, injects smart upsell bundles,
    and generates Razorpay test-mode payment links.
    """
    res = merchant_commerce_service.process_conversational_checkout(
        message=req.message,
        cart=req.cart,
        customer_info=req.customer_info,
        execute_checkout=req.execute_checkout or False
    )
    return res


@router.post("/ai-quote")
def request_ai_quote(req: AIQuoteRequest):
    """
    AI-to-AI quotation and negotiation endpoint.
    Evaluates requested items against merchant volume discount policies and inventory.
    """
    res = merchant_commerce_service.process_ai_to_ai_purchase(
        buyer_agent_id=req.buyer_agent_id,
        spending_token_limit_inr=req.spending_token_limit_inr,
        requested_items=[item.dict() for item in req.items],
        negotiation_requested=req.request_volume_discount or True
    )
    return res


@router.post("/ai-buy")
def execute_ai_buy(
    req: AIBuyRequest,
    x_buyer_agent_id: Optional[str] = Header(None),
    x_spending_token_limit: Optional[float] = Header(None),
    x_idempotency_key: Optional[str] = Header(None)
):
    """
    Autonomous AI-to-AI purchase execution endpoint.
    Validates buyer spending token limits, negotiates bounded bulk discounts,
    generates Razorpay payment links, and writes to the immutable audit trail.
    """
    buyer_id = x_buyer_agent_id or req.buyer_agent_id
    token_limit = x_spending_token_limit or req.spending_token_limit_inr
    idemp_key = x_idempotency_key or req.idempotency_key

    res = merchant_commerce_service.process_ai_to_ai_purchase(
        buyer_agent_id=buyer_id,
        spending_token_limit_inr=token_limit,
        requested_items=[item.dict() for item in req.items],
        negotiation_requested=req.negotiation_requested or True,
        idempotency_key=idemp_key
    )
    return res


@router.post("/campaigns/create")
def create_growth_campaign(req: GrowthCampaignRequest):
    """
    Autonomous Marketing Growth Campaign Orchestrator.
    Deducts allocated funds from Marketing department budget, generates promotional Razorpay links,
    and tracks projected ROAS and incremental sales.
    """
    res = merchant_commerce_service.create_growth_campaign(
        campaign_name=req.name,
        target_audience=req.target_audience,
        discount_pct=req.discount_pct,
        allocated_marketing_budget=req.allocated_marketing_budget,
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
    return merchant_commerce_service.simulate_failure_mode(
        failure_type=req.failure_type,
        custom_payload=req.custom_payload
    )
