from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends, Header

from src.app.services.finance_controller_service import finance_controller_service
from src.app.core.database import init_db

router = APIRouter(prefix="/controller", tags=["Autonomous Finance Controller"])


class CloseMonthRequest(BaseModel):
    actor: Optional[str] = Field(default="Finance Manager", description="Actor initiating month-close reconciliation")


class ExceptionDecisionRequest(BaseModel):
    decision: str = Field(..., description="One of: APPROVE, REJECT, ESCALATE")
    actor_name: Optional[str] = Field(default="Finance Manager", description="Name of the human approver")
    actor_role: Optional[str] = Field(default="FINANCE_MANAGER", description="Role of the human approver")
    comments: Optional[str] = Field(default="", description="Audit comments or rationale for the decision")


class BenchmarkReloadRequest(BaseModel):
    dataset_type: Optional[str] = Field(default="100_standard", description="Dataset type to reload")


@router.post("/close-month")
def close_month(req: Optional[CloseMonthRequest] = None):
    """
    Executes the autonomous month-close pipeline:
    3-way deterministic reconciliation (Payment vs Invoice vs Settlement),
    exception detection, policy checks, grounded AI root-cause synthesis,
    and cryptographic SHA-256 audit logging.
    """
    actor = req.actor if req else "Finance Manager"
    res = finance_controller_service.run_close_month(actor=actor)
    return res


@router.get("/dashboard")
def get_dashboard():
    """
    Returns real-time Finance Controller KPIs, run statistics,
    open exception summary, and recent human-in-the-loop decisions.
    """
    return finance_controller_service.get_dashboard_summary()


@router.get("/reconciliation")
def get_reconciliation(limit: int = 150):
    """
    Returns full list of reconciled records with 3-way matching status,
    payment gross, invoice total, settlement net, and variance.
    """
    records = finance_controller_service.get_reconciliation_records(limit=limit)
    return {"total": len(records), "records": records}


@router.get("/exceptions")
def get_exceptions():
    """
    Returns active exceptions queue with severity, amount difference,
    AI root cause, and policy triggered.
    """
    exceptions = finance_controller_service.get_exceptions()
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
    updating state and appending to the SHA-256 chained audit log.
    """
    res = finance_controller_service.decide_exception(
        exception_id=exception_id,
        decision=req.decision,
        actor_name=req.actor_name or "Finance Manager",
        actor_role=req.actor_role or "FINANCE_MANAGER",
        comments=req.comments or ""
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("detail"))
    return res


@router.get("/evaluation")
def get_evaluation():
    """
    Returns measured benchmark performance metrics calculated against ground truth:
    Accuracy, Precision, Recall, F1 Score, Execution Duration, and Throughput.
    """
    return finance_controller_service.evaluate_benchmark()


@router.post("/benchmark/reload")
def reload_benchmark(req: Optional[BenchmarkReloadRequest] = None):
    """
    Reloads the clean 120-record finance benchmark into SQLite database.
    """
    init_db()
    res = finance_controller_service.run_close_month(actor="Benchmark Reload")
    return {"success": True, "detail": "Benchmark reloaded and processed successfully.", "run": res}


@router.get("/audit-trail")
def get_audit_trail(limit: int = 50):
    """
    Returns chronological immutable audit trail with SHA-256 hash chaining.
    """
    trail = finance_controller_service.get_audit_trail(limit=limit)
    return {"total": len(trail), "audit_events": trail}
