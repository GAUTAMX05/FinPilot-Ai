import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from src.app.graphs.state import FinanceControllerState
from src.app.tools.finance_tools import (
    check_department_budget,
    forecast_department_budget,
    simulate_expense_affordability,
    get_company_financial_health_score,
    recommend_budget_reallocation,
)
from src.app.core.config import settings

logger = logging.getLogger("BudgetControllerAgent")

budget_llm = ChatOpenAI(
    model=settings.SUB_AGENT_MODEL,
    temperature=0.1,
    api_key=settings.OPENAI_API_KEY if settings.OPENAI_API_KEY else "sk-placeholder"
).bind_tools([
    check_department_budget,
    forecast_department_budget,
    simulate_expense_affordability,
    get_company_financial_health_score,
    recommend_budget_reallocation,
])


BUDGET_PROMPT = """
You are the AI Budget Governance, Runway & Forecasting Specialist.
Your responsibilities:
1. Fetch and analyze department budget utilization, monthly run-rates, and year-end overrun forecasts.
2. If asked "Are we overspending?", analyze Budget vs Actual vs Run-rate vs Fiscal year elapsed (Month 5/12).
3. If asked "Can we afford this?", call simulate_expense_affordability to evaluate runway impact.
4. Report all currency amounts in Indian Rupees (₹) with comma formatting.
5. Emphasize why variance occurred and what management should do.
"""


async def budget_controller_agent(state: FinanceControllerState) -> Dict[str, Any]:
    messages = state.get("messages", [])
    try:
        response = await budget_llm.ainvoke([SystemMessage(content=BUDGET_PROMPT)] + messages)
        return {
            "messages": [response],
            "next": "finance_controller_agent",
        }
    except Exception as e:
        logger.error(f"Budget controller error: {e}")
        return {"next": "finance_controller_agent"}
