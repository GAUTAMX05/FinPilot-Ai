from src.app.api.endpoints.auth import router as auth_router
from src.app.api.endpoints.audit import router as audit_router
from src.app.api.endpoints.users import router as users_router
from src.app.api.endpoints.intelligence import router as intelligence_router
from src.app.api.endpoints.agent_chat import router as chat_router
from src.app.api.endpoints.budgets import router as budgets_router
from src.app.api.endpoints.invoices import router as invoices_router
from src.app.api.endpoints.approvals import router as approvals_router
from src.app.api.endpoints.reconciliation import router as reconciliation_router
from src.app.api.endpoints.cash_flow import router as cash_flow_router
from src.app.api.endpoints.employee_finance import router as employee_finance_router
from src.app.api.endpoints.payroll import router as payroll_router
from src.app.api.endpoints.notifications import router as notifications_router
from src.app.api.endpoints.simulation import router as simulation_router

__all__ = [
    "auth_router",
    "audit_router",
    "users_router",
    "intelligence_router",
    "chat_router",
    "budgets_router",
    "invoices_router",
    "approvals_router",
    "reconciliation_router",
    "cash_flow_router",
    "employee_finance_router",
    "payroll_router",
    "notifications_router",
    "simulation_router",
]
