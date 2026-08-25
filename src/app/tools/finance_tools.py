import logging
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
from src.app.services.budget_service import budget_service
from src.app.services.anomaly_service import anomaly_service
from src.app.services.invoice_service import invoice_service
from src.app.services.razorpay_service import razorpay_service
from src.app.services.audit_service import audit_service
from src.app.services.intelligence_service import intelligence_service
from src.app.core.config import settings

logger = logging.getLogger("FinanceTools")


@tool
def get_company_financial_health_score(
    caller_role: Optional[str] = None,
    caller_department: Optional[str] = None
) -> dict:
    """
    Computes the company's real-time AI Financial Health Score (0-100),
    including Budget Discipline, Liquidity Ratio, Invoice Risk, Spending Efficiency,
    Approval Backlog, and detailed explainability factors.
    """
    return intelligence_service.calculate_health_score(caller_role, caller_department)


@tool
def forecast_department_budget(
    department: Optional[str] = None,
    caller_role: Optional[str] = None,
    caller_department: Optional[str] = None
) -> dict:
    """
    Predicts year-end spending, monthly burn velocity, runway health, and
    deficit/surplus for a specific department or all authorized departments.
    """
    forecasts = intelligence_service.get_department_forecasts(caller_role, caller_department)
    if department:
        for f in forecasts:
            if f["department"].lower() == department.strip().lower():
                return f
        return {"error": f"Department '{department}' not found or unauthorized for your role."}
    return {"forecasts": forecasts}


@tool
def simulate_expense_affordability(
    amount: float,
    department: str,
    category: str = "General",
    description: str = "",
    caller_role: Optional[str] = None,
    caller_department: Optional[str] = None
) -> dict:
    """
    Evaluates whether the company/department can afford a planned expense.
    Calculates post-expense remaining balance, budget impact %, and year-end deficit probability.
    """
    try:
        return intelligence_service.simulate_affordability(
            amount=amount,
            department=department,
            category=category,
            description=description,
            user_role=caller_role,
            user_department=caller_department,
        )
    except PermissionError as pe:
        return {"error": str(pe)}
    except Exception as e:
        return {"error": f"Affordability simulation error: {e}"}


@tool
def detect_duplicate_invoice_similarity(
    vendor_name: str,
    amount: float,
    department: str,
    description: str = "",
    invoice_id: Optional[str] = None
) -> dict:
    """
    Scans the invoice repository for multi-attribute fuzzy duplicates
    comparing vendor name, amount proximity, department, and description.
    """
    return intelligence_service.detect_duplicate_similarity(
        vendor_name=vendor_name,
        amount=amount,
        department=department,
        description=description,
        invoice_id=invoice_id,
    )


@tool
def analyze_vendor_risk_profile(
    vendor_name: Optional[str] = None,
    caller_role: Optional[str] = None
) -> dict:
    """
    Provides vendor spending intelligence, invoice counts, average ticket,
    anomaly frequency, and vendor risk scores (0-100).
    """
    vendors = intelligence_service.get_vendor_intelligence()
    if vendor_name:
        for v in vendors:
            if v["vendor_name"].lower() == vendor_name.strip().lower():
                return v
        return {"error": f"Vendor '{vendor_name}' not found in invoice history."}
    return {"vendors": vendors}


@tool
def get_proactive_watchtower_alerts(
    caller_role: Optional[str] = None,
    caller_department: Optional[str] = None
) -> dict:
    """
    Returns prioritized proactive AI alerts (Critical Overruns, Spikes, Anomalies, Insights)
    generated continuously from actual financial records.
    """
    alerts = intelligence_service.get_watchtower_alerts(caller_role, caller_department)
    return {"alerts": alerts, "total_active_alerts": len(alerts)}


@tool
def recommend_budget_reallocation(
    target_department: str,
    caller_role: Optional[str] = None
) -> dict:
    """
    Analyzes all department surpluses and deficits, and recommends optimal
    budget reallocations to prevent projected deficits.
    """
    forecasts = intelligence_service.get_department_forecasts()
    target_forecast = next((f for f in forecasts if f["department"].lower() == target_department.lower()), None)
    
    if not target_forecast:
        return {"error": f"Target department '{target_department}' not found."}

    surplus_depts = [f for f in forecasts if not f["is_overrun"] and f["projected_surplus_amount"] > 100000]
    
    if not surplus_depts:
        return {"recommendation": "No departments currently hold sufficient surplus for safe reallocation."}

    best_source = max(surplus_depts, key=lambda x: x["projected_surplus_amount"])
    realloc_amt = min(target_forecast["projected_overrun_amount"], best_source["projected_surplus_amount"] * 0.5)

    return {
        "recommended_action": "BUDGET_REALLOCATION",
        "from_department": best_source["department"],
        "to_department": target_forecast["department"],
        "recommended_amount": round(realloc_amt, 2),
        "source_available_surplus": best_source["projected_surplus_amount"],
        "target_projected_deficit": target_forecast["projected_overrun_amount"],
        "justification": f"Reallocating ₹{realloc_amt:,.2f} from {best_source['department']} eliminates deficit pressure in {target_forecast['department']} while maintaining safe operational reserves in {best_source['department']}.",
    }


@tool
def generate_executive_financial_report(
    caller_role: Optional[str] = None,
    caller_department: Optional[str] = None
) -> dict:
    """
    Generates a structured executive financial performance report
    synthesizing Health Score, Budget Forecasts, Top Risks, and Actionable Recommendations.
    """
    health = intelligence_service.calculate_health_score(caller_role, caller_department)
    forecasts = intelligence_service.get_department_forecasts(caller_role, caller_department)
    alerts = intelligence_service.get_watchtower_alerts(caller_role, caller_department)
    vendors = intelligence_service.get_vendor_intelligence()
    proposals = intelligence_service.get_proposals()

    return {
        "report_title": "Executive AI Financial Performance & Risk Intelligence Brief",
        "generated_at": datetime.now().isoformat(),
        "fiscal_year": intelligence_service.fiscal_year_label,
        "financial_health_score": health["overall_score"],
        "health_rating": health["rating"],
        "health_decomposition": health["explainability"],
        "department_forecasts": forecasts,
        "active_watchtower_alerts": alerts,
        "top_vendor_exposures": vendors[:3],
        "active_ai_proposals": proposals,
    }


@tool
def check_department_budget(
    department: str,
    caller_role: Optional[str] = None,
    caller_department: Optional[str] = None
) -> dict:
    """
    Retrieves the allocated budget, current spent amount, pending approvals,
    and remaining balance for a specific department (e.g., Engineering, Marketing, Sales, Operations, HR).
    Enforces RBAC department isolation for Department Heads.
    """
    if caller_role == "DEPARTMENT_HEAD" and caller_department:
        if department.strip().lower() != caller_department.strip().lower():
            return {
                "error": f"Permission Denied: You do not have permission to access {department} department financial data. You are only authorized for the {caller_department} department."
            }

    res = budget_service.get_department_budget(department, caller_role, caller_department)
    if not res:
        return {"error": f"Department '{department}' not found or access restricted."}
    return res


@tool
def audit_invoice_compliance(
    vendor_name: str,
    subtotal: float,
    tax_gst: float,
    total_amount: float,
    department: str,
    caller_role: Optional[str] = None,
    caller_department: Optional[str] = None
) -> dict:
    """
    Audits an invoice for tax consistency, duplicate vendor claims, budget availability,
    and policy compliance.
    """
    if caller_role == "DEPARTMENT_HEAD" and caller_department:
        if department.strip().lower() != caller_department.strip().lower():
            return {
                "error": f"Permission Denied: As {caller_department} Head, you cannot audit invoices for {department}."
            }

    invoice_payload = {
        "vendor_name": vendor_name,
        "subtotal": subtotal,
        "tax_gst": tax_gst,
        "total_amount": total_amount,
        "department": department,
    }
    return anomaly_service.audit_invoice(invoice_payload)


@tool
def create_expense_request(
    department: str,
    amount: float,
    vendor_name: str,
    description: str,
    caller_id: Optional[str] = None,
    caller_name: Optional[str] = None,
    caller_role: Optional[str] = None,
    caller_department: Optional[str] = None
) -> dict:
    """
    Submits an expense / invoice payment request.
    If caller is Auditor, this is prohibited.
    If caller is Department Head, must belong to their department.
    """
    if caller_role == "AUDITOR":
        return {
            "error": "Permission Denied: Auditors cannot create or modify financial requests. You may only audit or flag transactions."
        }

    if caller_role == "DEPARTMENT_HEAD" and caller_department:
        if department.strip().lower() != caller_department.strip().lower():
            return {
                "error": f"Permission Denied: You can only create expense claims for your assigned department ({caller_department})."
            }

    requires_hitl = amount >= settings.HITL_APPROVAL_THRESHOLD_INR
    reserved = budget_service.reserve_budget(department, amount)
    
    invoice_record = invoice_service.add_invoice({
        "vendor_name": vendor_name,
        "department": department,
        "description": description,
        "total_amount": amount,
        "submitted_by_id": caller_id,
        "submitted_by_name": caller_name,
        "status": "pending_approval" if requires_hitl else "approved",
        "requires_hitl": requires_hitl,
    })

    audit_service.log_action(
        user_id=caller_id or "usr_agent",
        user_name=caller_name or "Agent Caller",
        role=caller_role or "FINANCE_MANAGER",
        action="CREATE_EXPENSE_REQUEST",
        entity="INVOICE",
        entity_id=invoice_record["invoice_id"],
        new_value=f"₹{amount:,.2f} INR ({department})",
        details=f"Created expense for {vendor_name}: {description}",
        risk_level="MEDIUM" if requires_hitl else "LOW",
    )

    return {
        "invoice_id": invoice_record["invoice_id"],
        "vendor_name": vendor_name,
        "department": department,
        "amount": amount,
        "requires_hitl_approval": requires_hitl,
        "status": invoice_record["status"],
        "budget_reserved": reserved,
    }


@tool
def generate_razorpay_payment_link(
    amount: float,
    description: str,
    vendor_name: str = "Vendor Partner",
    caller_role: Optional[str] = None
) -> dict:
    """
    Generates a secure Razorpay payment link for vendor disbursement or invoice settlement.
    Auditors and unauthorized roles are strictly blocked.
    """
    if caller_role == "AUDITOR":
        return {
            "error": "Permission Denied: As an Auditor, you do not have permission to generate payment links or disburse funds."
        }

    return razorpay_service.create_payment_link(
        amount_inr=amount,
        description=description,
        customer_name=vendor_name,
    )


@tool
def flag_transaction_for_review(
    invoice_id: str,
    reason: str,
    caller_id: Optional[str] = None,
    caller_name: Optional[str] = None,
    caller_role: Optional[str] = None,
) -> dict:
    """
    Allows an Auditor or Compliance Officer to flag a suspicious transaction or anomaly for review.
    """
    flag = audit_service.flag_transaction(
        user_id=caller_id or "usr_auditor",
        user_name=caller_name or "Auditor",
        role=caller_role or "AUDITOR",
        entity_id=invoice_id,
        reason=reason,
        risk_level="HIGH",
    )
    return {"success": True, "flag": flag, "message": f"Invoice {invoice_id} successfully flagged for review."}
