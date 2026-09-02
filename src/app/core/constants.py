# -*- coding: utf-8 -*-
"""
FinPilot AI — Core Financial Domain Constants & Governance Policies
===================================================================
This module centralizes all financial arithmetic rates, operational thresholds,
RBAC limits, and state definitions used across the FinPilot platform.

Why centralized constants matter:
1. Eliminates 'magic numbers' from reconciliation and tax calculations.
2. Ensures statutory compliance (e.g. standard 18% Indian GST).
3. Makes financial governance policies transparent, configurable, and auditable.
"""

# =============================================================================
# 1. STATUTORY TAX & GATEWAY PRICING CONSTANTS
# =============================================================================

# Standard Indian Goods & Services Tax (GST) rate for software and payment processing services
GST_RATE_STANDARD: float = 0.18

# Standard Razorpay Merchant Discount Rate (MDR) for domestic transaction processing (2.00%)
DEFAULT_GATEWAY_MDR_RATE: float = 0.02

# International or Corporate Credit Card MDR surcharge tier (2.48% - 2.66%)
GATEWAY_SURCHARGE_MDR_RATE: float = 0.0248


# =============================================================================
# 2. RECONCILIATION & EXCEPTION DETECTION THRESHOLDS
# =============================================================================

# Maximum variance (in INR) auto-resolved without human intervention to prevent operational drag
# Discrepancies <= ₹50.00 (e.g., fractional paise rounding or minor fee drift) are auto-booked
AUTO_RECONCILIATION_TOLERANCE_INR: float = 50.0

# Discrepancy threshold (in INR) requiring mandatory Executive CFO authorization
# High-value adjustments >= ₹10,000.00 cannot be approved by standard Finance Managers
CFO_APPROVAL_THRESHOLD_INR: float = 10000.0

# Maximum acceptable business day lag between transaction capture and bank settlement
# Settlements taking longer than T+2 (+ weekend buffer = 5 days) are flagged as TIMING_ANOMALY
PAYMENT_SETTLEMENT_MAX_LAG_DAYS: int = 5

# Ratio threshold for detecting partial settlement tranches vs rolling chargeback reserves (75%)
PARTIAL_SETTLEMENT_RATIO_THRESHOLD: float = 0.75


# =============================================================================
# 3. MERCHANT COMMERCE & AI NEGOTIATION POLICY
# =============================================================================

# Maximum discount percentage an autonomous AI merchant can grant in automated negotiation
MAX_NEGOTIATION_DISCOUNT_PERCENT: float = 12.0

# Minimum item quantity required to qualify for bulk tier negotiation
MIN_BULK_UNITS_FOR_DISCOUNT: int = 3

# Single-transaction autonomous checkout ceiling before human authorization is required
AUTONOMOUS_CHECKOUT_CAP_INR: float = 50000.0


# =============================================================================
# 4. MULTI-TENANCY & DEFAULT IDENTIFIERS
# =============================================================================

DEFAULT_TENANT_ID: str = "merchant_default"
GENESIS_AUDIT_HASH: str = "GENESIS_AUDIT_HASH_FINPILOT_2026"


# =============================================================================
# 5. CONTROLLER EXCEPTION LIFECYCLE STATES
# =============================================================================

# All valid operational states for a controller exception
VALID_EXCEPTION_STATES = {
    "OPEN",                     # Newly detected discrepancy awaiting review
    "REQUIRES_HUMAN_REVIEW",    # Policy triggered; requires human evaluation
    "INVESTIGATING",            # Under active review with AI diagnostic evidence
    "PENDING_APPROVAL",         # Journal voucher drafted; waiting for manager sign-off
    "HUMAN_APPROVED",           # Approved by authorized reviewer; ledger adjusted
    "HUMAN_REJECTED",           # Rejected by reviewer; flagged for vendor/customer dispute
    "ESCALATED_TO_CFO",         # High-value variance escalated for CFO executive sign-off
    "AUTO_RESOLVED",            # Resolved automatically within policy tolerance (<= ₹50)
    "RESOLVED"                  # Marked fully resolved
}

# Terminal states that cannot transition without explicit administrative override
TERMINAL_EXCEPTION_STATES = {
    "HUMAN_APPROVED",
    "HUMAN_REJECTED",
    "AUTO_RESOLVED",
    "RESOLVED"
}
