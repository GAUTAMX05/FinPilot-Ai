import logging
from typing import Optional
from fastapi import APIRouter, Depends

from src.app.core.auth_middleware import get_current_user
from src.app.services.cash_flow_service import cash_flow_service

logger = logging.getLogger("CashFlowApi")
router = APIRouter(prefix="/cash-flow", tags=["Cash Flow & Liquidity Forecasting"])


@router.get("/forecast")
def get_cash_forecast(current_user: dict = Depends(get_current_user)):
    """Calculates 7-Day, 30-Day, 90-Day, and Fiscal Year liquidity projections."""
    user_role = current_user.get("role")
    user_dept = current_user.get("department")
    res = cash_flow_service.generate_cash_forecast(user_role, user_dept)
    return {"success": True, "forecast": res}
