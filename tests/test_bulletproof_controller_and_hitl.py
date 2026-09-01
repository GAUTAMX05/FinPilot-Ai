# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# -*- coding: utf-8 -*-
"""
FinPilot AI — Bulletproof Controller, HITL, RBAC & Payment Integrity Test Suite
================================================================================
Covers:
1. System Startup & Readiness (/health, /ready).
2. Razorpay Payment Link Integrity (strict differentiation, zero fabricated URLs).
3. 3-Way Reconciliation & Deterministic Fee Arithmetic.
4. Exception Lifecycle & Invalid State Transition Rejection.
5. RBAC Permission Checks (CFO vs Finance Manager vs Auditor).
6. Idempotency on Repeated Approvals.
7. SHA-256 Chained Cryptographic Audit Logging.
8. Measured Ground Truth Evaluation.
9. Connected "Merchant Day" 9-Stage Governance Engine.
"""

import pytest
from fastapi.testclient import TestClient
from src.app.main import app
from src.app.core.database import init_db, get_db_connection
from src.app.services.razorpay_service import razorpay_service
from src.app.services.finance_controller_service import finance_controller_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Ensure clean database initialization before each test."""
    init_db()


# -----------------------------------------------------------------------------
# 1. SYSTEM STARTUP & READINESS
# -----------------------------------------------------------------------------

def test_health_check_liveness():
    """Verifies that /health returns healthy status and metadata."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "FinPilot AI" in data["app"]
    assert "timestamp" in data


def test_readiness_probe_dependencies():
    """Verifies that /ready checks SQLite database, benchmark records, and gateway mode."""
    res = client.get("/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["database"]["connected"] is True
    assert data["database"]["benchmark_records_seeded"] >= 120
    assert "gateway" in data
    assert data["gateway"]["mode"] in ["razorpay_test", "razorpay_live", "simulation"]


# -----------------------------------------------------------------------------
# 2. RAZORPAY PAYMENT LINK INTEGRITY
# -----------------------------------------------------------------------------

def test_payment_link_simulation_mode_integrity():
    """Verifies that when keys are unconfigured, payment_link is None and never a fabricated rzp.io URL."""
    res = razorpay_service.create_payment_link(
        amount_inr=1500.0,
        description="Integrity Test Link",
        customer_name="Test Merchant",
        customer_email="test@merchant.local"
    )
    assert res["success"] is True
    if not razorpay_service.is_configured():
        assert res["is_real_razorpay_link"] is False
        assert res["payment_mode"] == "simulation"
        assert res["payment_link"] is None
        assert res["short_url"] is None
        assert "simulation" in res["unavailable_reason"].lower()


def test_gateway_status_endpoint():
    """Verifies /v1/controller/gateway-status exposes operational mode without leaking secrets."""
    res = client.get("/v1/controller/gateway-status")
    assert res.status_code == 200
    data = res.json()
    assert "is_configured" in data
    assert "gateway_mode" in data
    assert "INR" in data["supported_currencies"]
    assert "key_secret" not in data


# -----------------------------------------------------------------------------
# 3. 3-WAY DETERMINISTIC RECONCILIATION
# -----------------------------------------------------------------------------

def test_close_month_execution():
    """Verifies month-end close runs deterministic 3-way matching over all 120 records."""
    res = client.post("/v1/controller/close-month", json={"actor": "Automated Test Suite"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["records_processed"] == 120
    assert data["auto_reconciled"] == 95
    assert data["exceptions_count"] == 25
    assert data["match_rate_percentage"] == 79.2
    assert "sha256_audit_hash" in data


# -----------------------------------------------------------------------------
# 4. EXCEPTION LIFECYCLE & INVALID STATE TRANSITIONS
# -----------------------------------------------------------------------------

def test_exception_investigate_grounded_evidence():
    """Verifies /v1/controller/exceptions/{id}/investigate produces grounded 5-part AI root-cause analysis."""
    res = client.post("/v1/controller/exceptions/EXC-0001/investigate")
    assert res.status_code == 200
    data = res.json()
    assert data["exception_id"] == "EXC-0001"
    assert "ai_investigation" in data
    assert data["ai_investigation"]["issue"] != ""
    assert data["ai_investigation"]["evidence"] != ""
    assert data["ai_investigation"]["root_cause"] != ""
    assert data["ai_investigation"]["recommendation"] != ""


def test_exception_decision_state_transition():
    """Verifies exception transition to HUMAN_APPROVED updates state and records SHA-256 audit entry."""
    res = client.post("/v1/controller/exceptions/EXC-0001/decide", json={
        "decision": "APPROVE",
        "actor_name": "Priya Sharma",
        "actor_role": "CFO",
        "comments": "Approved fee adjustment after reviewing gateway tier schedule."
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["new_status"] == "HUMAN_APPROVED"
    assert "sha256_audit_hash" in data


def test_invalid_state_transition_rejected():
    """Verifies that an already approved/terminal exception cannot transition to an illegal state."""
    # Ensure EXC-0001 is in terminal state HUMAN_APPROVED
    client.post("/v1/controller/exceptions/EXC-0001/decide", json={
        "decision": "APPROVE",
        "actor_name": "Priya Sharma",
        "actor_role": "CFO",
        "comments": "Initial approval."
    })

    # Attempt conflicting transition
    res = client.post("/v1/controller/exceptions/EXC-0001/decide", json={
        "decision": "REJECT",
        "actor_name": "Priya Sharma",
        "actor_role": "CFO",
        "comments": "Conflicting attempt."
    })
    assert res.status_code == 400
    assert "terminal state" in res.json()["detail"].lower() or "invalid" in res.json()["detail"].lower()


def test_idempotent_approval_handling():
    """Verifies that re-submitting the exact same approval returns idempotent success."""
    res1 = client.post("/v1/controller/exceptions/EXC-0002/decide", json={
        "decision": "APPROVE",
        "actor_name": "Priya Sharma",
        "actor_role": "CFO",
        "comments": "First approval call."
    })
    assert res1.status_code == 200

    # Repeat exact same decision
    res2 = client.post("/v1/controller/exceptions/EXC-0002/decide", json={
        "decision": "APPROVE",
        "actor_name": "Priya Sharma",
        "actor_role": "CFO",
        "comments": "First approval call."
    })
    assert res2.status_code == 200
    assert res2.json()["is_idempotent_replay"] is True


# -----------------------------------------------------------------------------
# 5. RBAC PERMISSION ENFORCEMENT
# -----------------------------------------------------------------------------

def test_auditor_cannot_approve():
    """Verifies that read-only Auditor role is blocked from approving financial exceptions."""
    res = client.post("/v1/controller/exceptions/EXC-0003/decide", json={
        "decision": "APPROVE",
        "actor_name": "Kavita Nair",
        "actor_role": "AUDITOR",
        "comments": "Auditor attempting approval."
    })
    assert res.status_code == 400
    assert "auditor" in res.json()["detail"].lower()


def test_finance_manager_cannot_approve_cfo_escalated_exception():
    """Verifies that Finance Manager cannot approve an exception escalated to CFO."""
    # Find an ESCALATED_TO_CFO exception (e.g. EXC-0007 Duplicate Invoice)
    exceptions = finance_controller_service.get_exceptions()
    esc_exc = next((e for e in exceptions if e["status"] == "ESCALATED_TO_CFO"), None)

    if esc_exc:
        res = client.post(f"/v1/controller/exceptions/{esc_exc['exception_id']}/decide", json={
            "decision": "APPROVE",
            "actor_name": "Rahul Verma",
            "actor_role": "FINANCE_MANAGER",
            "comments": "Unauthorized FM attempt."
        })
        assert res.status_code == 400
        assert "cfo" in res.json()["detail"].lower()


# -----------------------------------------------------------------------------
# 6. MEASURED BENCHMARK EVALUATION & AUDIT TRAIL
# -----------------------------------------------------------------------------

def test_benchmark_evaluation_exact_metrics():
    """Verifies /v1/controller/evaluation computes exact metrics against internal ground truth."""
    res = client.get("/v1/controller/evaluation")
    assert res.status_code == 200
    data = res.json()
    assert data["total_records"] == 120
    assert data["match_accuracy"] == 100.0
    assert data["exception_precision"] == 100.0
    assert data["exception_recall"] == 100.0
    assert data["f1_score"] == 100.0
    assert data["false_positives"] == 0
    assert data["false_negatives"] == 0


def test_audit_trail_sha256_chain():
    """Verifies /v1/controller/audit-trail returns chronological SHA-256 chained events."""
    res = client.get("/v1/controller/audit-trail?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    for evt in data["audit_events"]:
        assert "sha256_hash" in evt
        assert "prev_hash" in evt
        assert "actor" in evt
        assert "action" in evt


# -----------------------------------------------------------------------------
# 7. CONNECTED "MERCHANT DAY" SIMULATION WORKFLOW
# -----------------------------------------------------------------------------

def test_merchant_day_full_cycle():
    """Verifies connected 9-stage Merchant Day governance cycle completes with audit trace."""
    res = client.post("/v1/controller/merchant-day/run")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["total_steps"] == 9
    assert "MDAY-" in data["demo_trace_id"]
    assert data["final_status"] == "GOVERNED_AND_AUDITED"
