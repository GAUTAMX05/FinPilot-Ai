import hmac
import hashlib
import time
import base64
import json
from enum import Enum
from typing import Set, Dict, Any, Optional

SECRET_KEY = "ai-finance-controller-super-secret-key-2026"


class Permission(str, Enum):
    VIEW_ALL_FINANCIAL_DATA = "VIEW_ALL_FINANCIAL_DATA"
    VIEW_DEPARTMENT_DATA = "VIEW_DEPARTMENT_DATA"
    VIEW_OWN_DEPARTMENT_DATA = "VIEW_OWN_DEPARTMENT_DATA"
    CREATE_EXPENSE_REQUEST = "CREATE_EXPENSE_REQUEST"
    APPROVE_EXPENSE = "APPROVE_EXPENSE"
    REJECT_EXPENSE = "REJECT_EXPENSE"
    MANAGE_BUDGET = "MANAGE_BUDGET"
    MODIFY_BUDGET = "MODIFY_BUDGET"
    VIEW_INVOICES = "VIEW_INVOICES"
    CREATE_INVOICE = "CREATE_INVOICE"
    AUDIT_INVOICE = "AUDIT_INVOICE"
    FLAG_TRANSACTION = "FLAG_TRANSACTION"
    GENERATE_PAYMENT_LINK = "GENERATE_PAYMENT_LINK"
    MANAGE_RAZORPAY = "MANAGE_RAZORPAY"
    VIEW_LIQUIDITY = "VIEW_LIQUIDITY"
    VIEW_FINANCIAL_REPORTS = "VIEW_FINANCIAL_REPORTS"
    VIEW_AUDIT_LOGS = "VIEW_AUDIT_LOGS"
    EXPORT_REPORTS = "EXPORT_REPORTS"
    MANAGE_USERS = "MANAGE_USERS"
    FINAL_APPROVAL = "FINAL_APPROVAL"


class Role(str, Enum):
    CFO = "CFO"
    FINANCE_MANAGER = "FINANCE_MANAGER"
    DEPARTMENT_HEAD = "DEPARTMENT_HEAD"
    AUDITOR = "AUDITOR"


ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.CFO: {
        Permission.VIEW_ALL_FINANCIAL_DATA,
        Permission.VIEW_DEPARTMENT_DATA,
        Permission.VIEW_OWN_DEPARTMENT_DATA,
        Permission.CREATE_EXPENSE_REQUEST,
        Permission.APPROVE_EXPENSE,
        Permission.REJECT_EXPENSE,
        Permission.MANAGE_BUDGET,
        Permission.MODIFY_BUDGET,
        Permission.VIEW_INVOICES,
        Permission.CREATE_INVOICE,
        Permission.AUDIT_INVOICE,
        Permission.FLAG_TRANSACTION,
        Permission.GENERATE_PAYMENT_LINK,
        Permission.MANAGE_RAZORPAY,
        Permission.VIEW_LIQUIDITY,
        Permission.VIEW_FINANCIAL_REPORTS,
        Permission.VIEW_AUDIT_LOGS,
        Permission.EXPORT_REPORTS,
        Permission.MANAGE_USERS,
        Permission.FINAL_APPROVAL,
    },
    Role.FINANCE_MANAGER: {
        Permission.VIEW_ALL_FINANCIAL_DATA,
        Permission.VIEW_DEPARTMENT_DATA,
        Permission.VIEW_OWN_DEPARTMENT_DATA,
        Permission.CREATE_EXPENSE_REQUEST,
        Permission.APPROVE_EXPENSE,
        Permission.REJECT_EXPENSE,
        Permission.MANAGE_BUDGET,
        Permission.VIEW_INVOICES,
        Permission.CREATE_INVOICE,
        Permission.AUDIT_INVOICE,
        Permission.FLAG_TRANSACTION,
        Permission.GENERATE_PAYMENT_LINK,
        Permission.MANAGE_RAZORPAY,
        Permission.VIEW_LIQUIDITY,
        Permission.VIEW_FINANCIAL_REPORTS,
        Permission.EXPORT_REPORTS,
    },
    Role.DEPARTMENT_HEAD: {
        Permission.VIEW_OWN_DEPARTMENT_DATA,
        Permission.CREATE_EXPENSE_REQUEST,
        Permission.APPROVE_EXPENSE,
        Permission.REJECT_EXPENSE,
        Permission.VIEW_INVOICES,
    },
    Role.AUDITOR: {
        Permission.VIEW_ALL_FINANCIAL_DATA,
        Permission.VIEW_DEPARTMENT_DATA,
        Permission.VIEW_INVOICES,
        Permission.AUDIT_INVOICE,
        Permission.FLAG_TRANSACTION,
        Permission.VIEW_LIQUIDITY,
        Permission.VIEW_FINANCIAL_REPORTS,
        Permission.VIEW_AUDIT_LOGS,
        Permission.EXPORT_REPORTS,
    },
}


def hash_password(password: str, salt: str = "ai_finance_salt_2026") -> str:
    """Computes a SHA-256 password hash with salt."""
    salted = f"{salt}:{password}".encode("utf-8")
    return hashlib.sha256(salted).hexdigest()


def verify_password(plain_password: str, password_hash: str, salt: str = "ai_finance_salt_2026") -> bool:
    """Verifies a plain password against the stored hash."""
    return hmac.compare_digest(hash_password(plain_password, salt), password_hash)


def create_access_token(user_data: Dict[str, Any], expires_in_seconds: int = 86400) -> str:
    """Creates a signed HMAC token carrying user claims."""
    payload = {
        **user_data,
        "exp": int(time.time()) + expires_in_seconds,
        "iat": int(time.time()),
    }
    payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")
    
    signature = hmac.new(SECRET_KEY.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a signed token."""
    try:
        parts = token.strip().split(".")
        if len(parts) != 2:
            return None
        payload_b64, signature = parts
        
        expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        
        # Add padding back if necessary
        padded_b64 = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload_json = base64.urlsafe_b64decode(padded_b64.encode("utf-8")).decode("utf-8")
        payload = json.loads(payload_json)
        
        if payload.get("exp", 0) < int(time.time()):
            return None  # Expired
            
        return payload
    except Exception:
        return None


def user_has_permission(role: Role, permission: Permission) -> bool:
    """Checks if a given role possesses a specific permission."""
    perms = ROLE_PERMISSIONS.get(role, set())
    return permission in perms
