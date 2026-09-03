import logging
from typing import Dict, Any
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
from src.app.services.llm_provider import build_chat_llm

logger = logging.getLogger("InvoiceAuditorAgent")


def _build_auditor_llm():
    llm = build_chat_llm(purpose="subagent", temperature=0.1)
    if llm is None:
        return None
    try:
        return llm.bind_tools([
            audit_invoice_compliance,
            create_expense_request,
            detect_duplicate_invoice_similarity,
            analyze_vendor_risk_profile,
            flag_transaction_for_review,
            generate_razorpay_payment_link,
        ])
    except Exception as e:
        logger.warning(f"[InvoiceAuditor] bind_tools failed, using unbound LLM: {e}")
        return llm


auditor_llm = _build_auditor_llm()


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
    if auditor_llm is None:
        logger.info("[InvoiceAuditor] No LLM configured; skipping to deterministic controller.")
        return {"next": "finance_controller_agent"}
    try:
        response = await auditor_llm.ainvoke([SystemMessage(content=AUDITOR_PROMPT)] + messages)

        tool_calls = getattr(response, "tool_calls", None) or []
        if tool_calls:
            tool_call = tool_calls[0]
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
