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

from src.app.core.rbac import Role, Permission, user_has_permission
from src.app.services.auth_service import auth_service
from src.app.services.budget_service import budget_service
from src.app.services.invoice_service import invoice_service
from src.app.services.audit_service import audit_service
from src.app.tools.finance_tools import check_department_budget, create_expense_request, generate_razorpay_payment_link


def test_rbac_permissions_matrix():
    print("1. Testing RBAC Permissions Matrix...")
    # CFO
    assert user_has_permission(Role.CFO, Permission.FINAL_APPROVAL) is True
    assert user_has_permission(Role.CFO, Permission.MANAGE_USERS) is True
    assert user_has_permission(Role.CFO, Permission.MODIFY_BUDGET) is True

    # Finance Manager
    assert user_has_permission(Role.FINANCE_MANAGER, Permission.AUDIT_INVOICE) is True
    assert user_has_permission(Role.FINANCE_MANAGER, Permission.FINAL_APPROVAL) is False
    assert user_has_permission(Role.FINANCE_MANAGER, Permission.MANAGE_USERS) is False

    # Department Head
    assert user_has_permission(Role.DEPARTMENT_HEAD, Permission.VIEW_OWN_DEPARTMENT_DATA) is True
    assert user_has_permission(Role.DEPARTMENT_HEAD, Permission.VIEW_ALL_FINANCIAL_DATA) is False
    assert user_has_permission(Role.DEPARTMENT_HEAD, Permission.MANAGE_USERS) is False

    # Auditor
    assert user_has_permission(Role.AUDITOR, Permission.VIEW_AUDIT_LOGS) is True
    assert user_has_permission(Role.AUDITOR, Permission.FLAG_TRANSACTION) is True
    assert user_has_permission(Role.AUDITOR, Permission.APPROVE_EXPENSE) is False
    assert user_has_permission(Role.AUDITOR, Permission.MODIFY_BUDGET) is False
    assert user_has_permission(Role.AUDITOR, Permission.GENERATE_PAYMENT_LINK) is False

    print("✓ RBAC permissions matrix verified successfully.")


def test_cfo_role():
    print("\n2. Testing CFO Role...")
    auth_res = auth_service.authenticate_user("cfo@aifinance.local", "password123")
    assert auth_res is not None
    user = auth_res["user"]
    assert user["role"] == "CFO"

    # Can view all departments
    all_depts = budget_service.get_all_departments(user["role"], user["department"])
    assert len(all_depts) >= 5, "CFO must see all 5 departments"

    # Can reallocate budget
    realloc_res = budget_service.reallocate_budget(
        from_department="Marketing",
        to_department="Engineering",
        amount=10000.0,
        user_id=user["id"],
        user_name=user["name"],
        role=user["role"],
        reason="Q3 Test Reallocation",
    )
    assert realloc_res["success"] is True

    # Can view audit logs
    logs = audit_service.get_audit_logs()
    assert len(logs) > 0
    print("✓ CFO role verified: Full access, reallocation, and audit visibility.")


def test_finance_manager_role():
    print("\n3. Testing Finance Manager Role...")
    auth_res = auth_service.authenticate_user("finance.manager@aifinance.local", "password123")
    assert auth_res is not None
    user = auth_res["user"]
    assert user["role"] == "FINANCE_MANAGER"

    # Can view all departments
    depts = budget_service.get_all_departments(user["role"], user["department"])
    assert len(depts) >= 5

    # Can generate payment link
    link_res = generate_razorpay_payment_link.invoke({
        "amount": 25000.0,
        "description": "Vendor software settlement",
        "caller_role": user["role"],
    })
    assert "short_url" in link_res or link_res.get("success") is True
    print("✓ Finance Manager role verified: Operational capabilities active.")


def test_department_head_isolation():
    print("\n4. Testing Department Head Data Isolation & Segregation of Duties...")
    auth_res = auth_service.authenticate_user("engineering.head@aifinance.local", "password123")
    assert auth_res is not None
    user = auth_res["user"]
    assert user["role"] == "DEPARTMENT_HEAD"
    assert user["department"] == "Engineering"

    # 1. Department Filtering
    depts = budget_service.get_all_departments(user["role"], user["department"])
    assert list(depts.keys()) == ["Engineering"], "Department Head must ONLY see their assigned department"

    # 2. Blocked from accessing other departments
    blocked_budget = budget_service.get_department_budget("Marketing", user["role"], user["department"])
    assert blocked_budget is None, "Department Head must be blocked from other departments"

    # 3. AI Tool Security Boundary
    ai_tool_check = check_department_budget.invoke({
        "department": "Marketing",
        "caller_role": user["role"],
        "caller_department": user["department"],
    })
    assert "error" in ai_tool_check or "Permission Denied" in str(ai_tool_check)
    print(f"AI Tool Security Response for Marketing: {ai_tool_check.get('error')}")

    print("✓ Department Head verified: Department-scoped data isolation enforced.")


def test_auditor_role_restrictions():
    print("\n5. Testing Auditor Read-Only & Flagging Capabilities...")
    auth_res = auth_service.authenticate_user("auditor@aifinance.local", "password123")
    assert auth_res is not None
    user = auth_res["user"]
    assert user["role"] == "AUDITOR"

    # 1. Auditor can view all audit logs
    logs = audit_service.get_audit_logs()
    assert len(logs) > 0

    # 2. Auditor can flag suspicious transaction
    flag_res = audit_service.flag_transaction(
        user_id=user["id"],
        user_name=user["name"],
        role=user["role"],
        entity_id="INV-2026-003",
        reason="Suspicious GST mismatch pattern",
        risk_level="HIGH",
    )
    assert flag_res["status"] == "OPEN"

    # 3. Auditor blocked from creating payment link
    tool_rzp = generate_razorpay_payment_link.invoke({
        "amount": 10000.0,
        "description": "Disbursement",
        "caller_role": user["role"],
    })
    assert "error" in tool_rzp and "Permission Denied" in tool_rzp["error"]

    # 4. Auditor blocked from creating expense claims
    tool_claim = create_expense_request.invoke({
        "department": "Engineering",
        "amount": 25000.0,
        "vendor_name": "Test Vendor",
        "description": "Test",
        "caller_role": user["role"],
    })
    assert "error" in tool_claim and "Permission Denied" in tool_claim["error"]

    print("✓ Auditor role verified: Read-only inspection and transaction flagging active.")


if __name__ == "__main__":
    test_rbac_permissions_matrix()
    test_cfo_role()
    test_finance_manager_role()
    test_department_head_isolation()
    test_auditor_role_restrictions()
    print("\n=======================================================")
    print("ALL 4 ROLES & RBAC SECURITY TESTS PASSED (100% SUCCESS)")
    print("=======================================================")
