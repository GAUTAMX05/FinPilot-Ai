import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from src.app.graphs.state import FinanceControllerState
from src.app.tools.finance_tools import (
    audit_invoice_compliance,
    create_expense_request,
    detect_duplicate_invoice_similarity,
    analyze_vendor_risk_profile,
    flag_transaction_for_review,
    generate_razorpay_payment_link,
)
from src.app.core.config import settings

logger = logging.getLogger("InvoiceAuditorAgent")

auditor_llm = ChatOpenAI(
    model=settings.SUB_AGENT_MODEL,
    temperature=0.1,
    api_key=settings.OPENAI_API_KEY if settings.OPENAI_API_KEY else "sk-placeholder"
).bind_tools([
    audit_invoice_compliance,
    create_expense_request,
    detect_duplicate_invoice_similarity,
    analyze_vendor_risk_profile,
    flag_transaction_for_review,
    generate_razorpay_payment_link,
])


AUDITOR_PROMPT = """
You are the AI Invoice Auditor & Anomaly Intelligence Specialist.
Your responsibilities:
1. Examine invoice details: vendor name, department, subtotal, GST/tax, and grand total.
2. Call `audit_invoice_compliance` to check tax math, duplicate charges, and budget policy caps.
3. Call `detect_duplicate_invoice_similarity` to check multi-vector duplicate similarity.
4. Call `analyze_vendor_risk_profile` to evaluate vendor history and anomalies.
5. If the amount is >= ₹50,000, clearly notify that Human-In-The-Loop (HITL) authorization is required.
"""


async def invoice_auditor_agent(state: FinanceControllerState) -> Dict[str, Any]:
    messages = state.get("messages", [])
    try:
        response = await auditor_llm.ainvoke([SystemMessage(content=AUDITOR_PROMPT)] + messages)
        
        if response.tool_calls:
            tool_call = response.tool_calls[0]
            tool_name = tool_call["name"]
            
            if tool_name == "create_expense_request":
                args = tool_call["args"]
                amount = float(args.get("amount", 0.0))
                if amount >= settings.HITL_APPROVAL_THRESHOLD_INR:
                    pending_details = {
                        "action": "expense_approval",
                        "department": args.get("department"),
                        "amount": amount,
                        "vendor_name": args.get("vendor_name"),
                        "description": args.get("description"),
                        "tool_call_id": tool_call["id"],
                    }
                    return {
                        "messages": [response],
                        "pending_approval": pending_details,
                        "next": "approval_node",
                    }

        return {
            "messages": [response],
            "next": "finance_controller_agent",
        }
    except Exception as e:
        logger.error(f"Invoice auditor error: {e}")
        return {"next": "finance_controller_agent"}
