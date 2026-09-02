# -*- coding: utf-8 -*-
import re
import math
import html
from typing import Optional, Any
from fastapi import HTTPException


# Maximum allowed monetary amount in INR: ₹100 Crores (1 Billion INR)
MAX_FINANCIAL_AMOUNT_INR = 1_000_000_000.0

# Allowed departments enum set
VALID_DEPARTMENTS = {"Engineering", "Marketing", "Sales", "Operations", "HR", "General", "Finance"}

# Suspicious SQL and Script patterns
INJECTION_PATTERNS = [
    re.compile(r"<\s*script[^>]*>", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"onerror\s*=", re.IGNORECASE),
    re.compile(r"onload\s*=", re.IGNORECASE),
    re.compile(r"(--|;|\bDROP\b|\bINSERT\b|\bDELETE\b|\bUPDATE\b|\bUNION\b|\bSELECT\b)\s+(TABLE|FROM|INTO|ALL)", re.IGNORECASE),
]


def sanitize_text(text: Optional[str], field_name: str = "Input", max_length: int = 1000, allow_empty: bool = True) -> str:
    """
    Sanitizes string inputs against script tags, XSS payloads, null bytes,
    and excessive length.
    """
    if text is None:
        if not allow_empty:
            raise HTTPException(status_code=422, detail=f"{field_name} is required and cannot be null.")
        return ""

    if not isinstance(text, str):
        raise HTTPException(status_code=422, detail=f"{field_name} must be a valid text string.")

    # Strip null bytes and control characters
    cleaned = text.replace("\x00", "").strip()

    if not cleaned and not allow_empty:
        raise HTTPException(status_code=422, detail=f"{field_name} cannot be empty.")

    if len(cleaned) > max_length:
        raise HTTPException(
            status_code=422,
            detail=f"{field_name} exceeds maximum allowed length of {max_length} characters (received {len(cleaned)}).",
        )

    # Detect malicious script patterns
    for pat in INJECTION_PATTERNS:
        if pat.search(cleaned):
            raise HTTPException(
                status_code=400,
                detail=f"Security violation: Malicious pattern or script injection detected in {field_name}.",
            )

    # Escape raw HTML characters to prevent stored XSS
    return html.escape(cleaned)


def validate_monetary_amount(
    amount: Any,
    field_name: str = "Amount",
    min_amount: float = 0.01,
    max_amount: float = MAX_FINANCIAL_AMOUNT_INR,
    allow_zero: bool = False
) -> float:
    """
    Validates monetary numbers against NaN, Inf, negative amounts, zero,
    and absurdly large balances.
    """
    if amount is None:
        raise HTTPException(status_code=422, detail=f"{field_name} is required.")

    try:
        val = float(amount)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail=f"{field_name} must be a valid numeric amount.")

    if math.isnan(val) or math.isinf(val):
        raise HTTPException(status_code=422, detail=f"{field_name} must be a finite valid number.")

    if allow_zero and val == 0.0:
        return 0.0

    if val < min_amount:
        if val < 0:
            raise HTTPException(status_code=400, detail=f"{field_name} cannot be negative (received ₹{val:,.2f}).")
        raise HTTPException(status_code=400, detail=f"{field_name} must be at least ₹{min_amount:,.2f} (received ₹{val:,.2f}).")

    if val > max_amount:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} exceeds system safety threshold of ₹{max_amount:,.2f} (received ₹{val:,.2f}).",
        )

    return round(val, 2)


def validate_percentage(pct: Any, field_name: str = "Percentage", min_pct: float = 0.0, max_pct: float = 100.0) -> float:
    """Validates percentage values between min_pct and max_pct."""
    if pct is None:
        raise HTTPException(status_code=422, detail=f"{field_name} is required.")

    try:
        val = float(pct)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail=f"{field_name} must be a valid numeric percentage.")

    if math.isnan(val) or math.isinf(val):
        raise HTTPException(status_code=422, detail=f"{field_name} must be a finite valid number.")

    if val < min_pct or val > max_pct:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be between {min_pct}% and {max_pct}% (received {val}%).",
        )

    return round(val, 2)


def validate_email_address(email: Optional[str]) -> str:
    """Validates corporate email format."""
    cleaned = sanitize_text(email, field_name="Email", max_length=120, allow_empty=False)
    email_regex = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    if not email_regex.match(cleaned):
        raise HTTPException(status_code=422, detail=f"Invalid email address format: '{cleaned}'.")
    return cleaned.lower()


def validate_department(dept: Optional[str]) -> str:
    """Validates department against organizational taxonomy."""
    cleaned = sanitize_text(dept, field_name="Department", max_length=50, allow_empty=False)
    for valid in VALID_DEPARTMENTS:
        if cleaned.lower() == valid.lower():
            return valid
    raise HTTPException(
        status_code=400,
        detail=f"Invalid department '{cleaned}'. Allowed departments: {sorted(list(VALID_DEPARTMENTS))}.",
    )
