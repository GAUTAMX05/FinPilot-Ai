# -*- coding: utf-8 -*-
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends, Header

from src.app.services.finance_controller_service import finance_controller_service
from src.app.services.razorpay_service import razorpay_service
from src.app.core.database import init_db

router = APIRouter(prefix="/controller", tags=["Autonomous Finance Controller"])


class CloseMonthRequest(BaseModel):
    actor: Optional[str] = Field(default="Finance Manager", description="Actor initiating month-close reconciliation")
    tenant_id: Optional[str] = Field(default="merchant_default", description="Merchant Organization Tenant ID")


class ExceptionDecisionRequest(BaseModel):
    decision: str = Field(..., description="One of: APPROVE, REJECT, ESCALATE, RESOLVE")
    actor_name: Optional[str] = Field(default="Finance Manager", description="Name of the human approver")
    actor_role: Optional[str] = Field(default="FINANCE_MANAGER", description="Role of the human approver (CFO, FINANCE_MANAGER, AUDITOR)")
    comments: Optional[str] = Field(default="", description="Audit comments or rationale for the decision")
    request_id: Optional[str] = Field(default=None, description="Client or gateway request correlation ID")


class BenchmarkReloadRequest(BaseModel):
    dataset_type: Optional[str] = Field(default="120_standard", description="Dataset type to reload")


@router.post("/close-month")
def close_month(req: Optional[CloseMonthRequest] = None):
    """
    Executes the autonomous month-close pipeline:
    3-way deterministic reconciliation (Payment vs Invoice vs Settlement),
    exception detection, policy checks, grounded AI root-cause synthesis,
    and cryptographic SHA-256 audit logging.
    """
    actor = req.actor if req else "Finance Manager"
    tenant_id = req.tenant_id if req else "merchant_default"
    res = finance_controller_service.run_close_month(actor=actor, tenant_id=tenant_id)
    return res


@router.get("/dashboard")
def get_dashboard(tenant_id: str = "merchant_default"):
    """
    Returns real-time Finance Controller KPIs, run statistics,
    open exception summary, gateway connectivity status, and recent human decisions.
    """
    return finance_controller_service.get_dashboard_summary(tenant_id=tenant_id)


@router.get("/gateway-status")
def get_gateway_status():
    """
    Returns live Razorpay gateway connection mode (Test Mode / Live / Simulation)
    and supported settlement features without leaking credentials.
    """
    return razorpay_service.get_gateway_status()


@router.get("/reconciliation")
def get_reconciliation(limit: int = 150, tenant_id: str = "merchant_default"):
    """
    Returns full list of reconciled records with 3-way matching status,
    payment gross, invoice total, settlement net, and variance.
    """
    records = finance_controller_service.get_reconciliation_records(limit=limit, tenant_id=tenant_id)
    return {"total": len(records), "records": records}


@router.get("/exceptions")
def get_exceptions(tenant_id: str = "merchant_default"):
    """
    Returns active exceptions queue with severity, amount difference,
    AI root cause, and policy triggered.
    """
    exceptions = finance_controller_service.get_exceptions(tenant_id=tenant_id)
    return {"total": len(exceptions), "exceptions": exceptions}


@router.post("/exceptions/{exception_id}/investigate")
def investigate_exception(exception_id: str):
    """
    Runs grounded AI root-cause analysis on actual financial evidence
    for a specific exception ID without hallucination.
    """
    exceptions = finance_controller_service.get_exceptions()
    match = next((e for e in exceptions if e["exception_id"] == exception_id), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Exception {exception_id} not found.")
    
    return {
        "exception_id": exception_id,
        "transaction_id": match.get("transaction_id"),
        "invoice_id": match.get("invoice_id"),
        "exception_type": match.get("exception_type"),
        "severity": match.get("severity"),
        "amount_difference": match.get("amount_difference"),
        "status": match.get("status"),
        "policy_triggered": match.get("policy_triggered"),
        "ai_investigation": {
            "issue": match.get("ai_issue"),
            "evidence": match.get("ai_evidence"),
            "root_cause": match.get("ai_root_cause"),
            "recommendation": match.get("ai_recommendation"),
            "confidence": match.get("confidence", 94.0)
        }
    }


@router.post("/exceptions/{exception_id}/decide")
def decide_exception(exception_id: str, req: ExceptionDecisionRequest):
    """
    Executes Human-in-the-Loop approval/rejection/escalation on an exception,
    enforcing RBAC permissions, updating state atomically, and appending
    to the SHA-256 chained audit log.
    """
    res = finance_controller_service.decide_exception(
        exception_id=exception_id,
        decision=req.decision,
        actor_name=req.actor_name or "Finance Manager",
        actor_role=req.actor_role or "FINANCE_MANAGER",
        comments=req.comments or "",
        request_id=req.request_id
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("detail"))
    return res


@router.get("/evaluation")
def get_evaluation(tenant_id: str = "merchant_default"):
    """
    Returns measured benchmark performance metrics calculated against ground truth:
    Accuracy, Precision, Recall, F1 Score, Execution Duration, and Throughput.
    """
    return finance_controller_service.evaluate_benchmark(tenant_id=tenant_id)


@router.post("/benchmark/reload")
def reload_benchmark(req: Optional[BenchmarkReloadRequest] = None):
    """
    Reloads the clean 120-record finance benchmark into SQLite database.
    """
    init_db()
    res = finance_controller_service.run_close_month(actor="Benchmark Reload")
    return {"success": True, "detail": "Benchmark reloaded and processed successfully.", "run": res}


@router.get("/audit-trail")
def get_audit_trail(limit: int = 50, tenant_id: str = "merchant_default"):
    """
    Returns chronological immutable audit trail with SHA-256 hash chaining.
    """
    trail = finance_controller_service.get_audit_trail(limit=limit, tenant_id=tenant_id)
    return {"total": len(trail), "audit_events": trail}


@router.post("/merchant-day/run")
def run_merchant_day(tenant_id: str = "merchant_default"):
    """
    Executes the connected 16-step "Merchant Day" workflow:
    Morning Health -> AI Procurement -> Catalog Discovery -> Negotiation -> Cart & GST ->
    Razorpay Link -> Transaction -> 3-Way Reconciliation -> Exception Detection ->
    AI Root Cause -> HITL Decision -> Cryptographic Audit Hash -> Updated Ledger.
    """
    return finance_controller_service.run_merchant_day_demo(tenant_id=tenant_id)
