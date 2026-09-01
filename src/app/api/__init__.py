from fastapi import APIRouter
from src.app.api.endpoints import (
    auth_router,
    audit_router,
    users_router,
    intelligence_router,
    chat_router,
    budgets_router,
    invoices_router,
    approvals_router,
    reconciliation_router,
    cash_flow_router,
    employee_finance_router,
    payroll_router,
    notifications_router,
    simulation_router,
    commerce_router,
    dataset_router,
    controller_router,
)

api_router = APIRouter()
api_router.include_router(controller_router)  # HERO API: Autonomous Finance Controller
api_router.include_router(auth_router)
api_router.include_router(audit_router)
api_router.include_router(users_router)
api_router.include_router(intelligence_router, prefix="/intelligence", tags=["Intelligence & Forecasting"])
api_router.include_router(chat_router)
api_router.include_router(budgets_router)
api_router.include_router(invoices_router)
api_router.include_router(approvals_router)
api_router.include_router(reconciliation_router)
api_router.include_router(cash_flow_router)
api_router.include_router(employee_finance_router, prefix="/employees", tags=["Employee Allowances & Financial Control"])
api_router.include_router(payroll_router, prefix="/payroll", tags=["Payroll & Form 16 Tax Reconciler"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["Financial Notifications & Alerts"])
api_router.include_router(simulation_router)
api_router.include_router(commerce_router)
api_router.include_router(dataset_router)

__all__ = ["api_router"]
