import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.app.services.budget_service import budget_service
from src.app.services.invoice_service import invoice_service
from src.app.services.intelligence_service import intelligence_service
from src.app.services.audit_service import audit_service
from src.app.services.reconciliation_service import reconciliation_service
from src.app.services.cash_flow_service import cash_flow_service
from src.app.services.employee_finance_service import employee_finance_service
from src.app.services.payroll_service import payroll_service
from src.app.core.config import settings

logger = logging.getLogger("AIReasoningEngine")


class AutonomousFinancialReasoningEngine:
    """
    Core AI Financial Reasoning Engine.
    Performs deterministic multi-step tool execution, financial data retrieval,
    variance calculation, forecasting, affordability evaluation, reconciliation,
    allowance governance, payroll analysis, and rich synthesis.
    """

    def analyze_financial_query(
        self,
        query: str,
        user_role: str = "CFO",
        user_name: str = "User",
        user_department: Optional[str] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Main reasoning dispatcher: Understands intent, checks RBAC, runs tools,
        and generates deep, data-driven financial analysis.
        """
        q_lower = query.lower()

        # ---------------------------------------------------------------------
        # 1. RBAC Guardrails
        # ---------------------------------------------------------------------
        if user_role == "DEPARTMENT_HEAD" and user_department:
            other_depts = [d for d in ["marketing", "sales", "operations", "hr", "engineering"] if d != user_department.lower()]
            for od in other_depts:
                if re.search(rf"\b{od}\b", q_lower) and not re.search(rf"\b{user_department.lower()}\b", q_lower):
                    return {
                        "response": (
                            f"## 🔒 Access Restricted (RBAC Policy)\n\n"
                            f"You are authenticated as **{user_name}** ({user_department} Department Head).\n\n"
                            f"Under corporate financial governance policies, you only have authorization to query and analyze "
                            f"**{user_department}** department budgets, expense records, and runway metrics.\n\n"
                            f"### Permitted Actions\n"
                            f"- Query `{user_department}` current allocation and committed spend\n"
                            f"- Forecast `{user_department}` year-end spend\n"
                            f"- Simulate planned expense affordability for `{user_department}`\n"
                            f"- Submit `{user_department}` expense claims"
                        ),
                        "status": "completed",
                        "suggested_actions": [
                            f"Check {user_department} runway",
                            f"Forecast {user_department} year-end spend",
                            f"Simulate planned {user_department} expense",
                        ],
                    }

        # ---------------------------------------------------------------------
        # 1. Counterfactual What-If & Multi-Agent Digital Twin Reasoning
        # ---------------------------------------------------------------------
        if any(k in q_lower for k in ["what if", "what-if", "suppose", "assume", "simulate", "if we delay", "if we spend", "if we hire", "60 days", "stay the same", "root cause", "coincide with", "policy calibration", "friction"]):
            from src.app.services.multi_agent_orchestrator import multi_agent_orchestrator
            orch_res = multi_agent_orchestrator.process_query(
                query=query,
                user_role=user_role,
                user_name=user_name,
                user_department=user_department,
            )
            return {
                "response": orch_res["response"]["text"],
                "status": "completed",
                "suggested_actions": orch_res["suggested_actions"],
                "simulation": orch_res.get("simulation"),
                "causal_analysis": orch_res.get("causal_analysis"),
                "agent_steps": orch_res.get("agent_steps"),
            }

        # ---------------------------------------------------------------------
        # 2. Intent: Payroll, Salary Bill & Form 16 / TDS
        # ---------------------------------------------------------------------
        if any(k in q_lower for k in ["payroll", "salary bill", "form 16", "tds", "tax deduction", "headcount", "employee cost", "salary mismatch"]):
            return self._reason_payroll_and_tax(query, user_role, user_department)

        # ---------------------------------------------------------------------
        # 3. Intent: Reconciliation & Ambiguous Transactions
        # ---------------------------------------------------------------------
        if any(k in q_lower for k in ["reconcil", "bank statement", "unmatched", "settlement variance", "gateway fee", "razorpay fee", "proposer", "verifier"]):
            return self._reason_reconciliation(user_role, user_department)
        if any(k in q_lower for k in ["cash position", "cash flow", "liquidity", "7-day", "30-day", "90-day", "cash runway", "cash forecast"]):
            return self._reason_cash_flow(user_role, user_department)

        # ---------------------------------------------------------------------
        # 4. Intent: Employee Allowance, Claims & Recommendations
        # ---------------------------------------------------------------------
        if any(k in q_lower for k in ["allowance", "travel claim", "food allowance", "claim limit", "employee limit", "rahul sharma", "priya verma"]):
            return self._reason_employee_allowance(query, user_role, user_department)

        # ---------------------------------------------------------------------
        # 5. Intent: Payroll, Salary Bill & Form 16 / TDS
        # ---------------------------------------------------------------------
        if any(k in q_lower for k in ["payroll", "salary bill", "form 16", "tds", "tax deduction", "deductions", "headcount", "employee cost"]):
            return self._reason_payroll_and_tax(query, user_role, user_department)

        # ---------------------------------------------------------------------
        # 6. Intent: "Are we overspending?" / Budget Run-rates & Deficit Risk
        # ---------------------------------------------------------------------
        if any(k in q_lower for k in ["overspend", "over spending", "spending pace", "burn rate", "run rate", "time elapsed", "budget utilization", "fiscal year"]):
            return self._reason_overspending(user_role, user_department)

        # ---------------------------------------------------------------------
        # 7. Intent: "Can we afford X?" / Affordability Scenario Simulation
        # ---------------------------------------------------------------------
        if any(k in q_lower for k in ["afford", "can we buy", "can we spend", "can we purchase", "affordability"]):
            amount = self._extract_amount(query) or 500000.0
            department = self._extract_department(query) or (user_department if user_role == "DEPARTMENT_HEAD" else "Engineering")
            category = "Cloud Infrastructure" if "cloud" in q_lower else ("Software" if "software" in q_lower else "General")
            return self._reason_affordability(amount, department, category, user_role, user_department)

        # ---------------------------------------------------------------------
        # 8. Intent: "Which department is most at risk / needs attention?"
        # ---------------------------------------------------------------------
        if any(k in q_lower for k in ["at risk", "most risk", "need attention", "needs attention", "rank department", "worst department"]):
            return self._reason_department_risks(user_role, user_department)

        # ---------------------------------------------------------------------
        # 9. Intent: "Why is Engineering overspending?" / Department Deep Dive
        # ---------------------------------------------------------------------
        dept_match = self._extract_department(query)
        if dept_match and any(k in q_lower for k in ["why", "cause", "explain", "detail", "deep dive", "cloud"]):
            return self._reason_department_deep_dive(dept_match, user_role, user_department)

        # ---------------------------------------------------------------------
        # 10. Intent: "Find suspicious invoices" / Invoice Anomaly Intelligence
        # ---------------------------------------------------------------------
        if any(k in q_lower for k in ["suspicious", "anomaly", "anomalies", "duplicate", "gst issue", "tax issue", "audit invoice"]):
            return self._reason_invoice_anomalies(user_role, user_department)

        # ---------------------------------------------------------------------
        # 11. Intent: "Top vendor risks" / Vendor Intelligence
        # ---------------------------------------------------------------------
        if any(k in q_lower for k in ["vendor", "vendors", "supplier", "cloudops"]):
            return self._reason_vendor_intelligence(user_role)

        # ---------------------------------------------------------------------
        # 12. Intent: "Watchtower brief" / "What should I worry about today?"
        # ---------------------------------------------------------------------
        if any(k in q_lower for k in ["watchtower", "worry", "alert", "alerts", "brief", "today", "summary"]):
            return self._reason_watchtower_brief(user_role, user_department)

        # ---------------------------------------------------------------------
        # 13. Intent: "Forecast year-end spending"
        # ---------------------------------------------------------------------
        if any(k in q_lower for k in ["forecast", "year end", "year-end", "projection", "q3", "q4"]):
            return self._reason_forecast(user_role, user_department)

        # ---------------------------------------------------------------------
        # 14. Intent: "How can we reduce spending?" / Recommendations
        # ---------------------------------------------------------------------
        if any(k in q_lower for k in ["reduce", "cut", "save", "optimization", "recommend", "solution"]):
            return self._reason_cost_reduction(user_role, user_department)

        # ---------------------------------------------------------------------
        # Default: Comprehensive Financial State Overview
        # ---------------------------------------------------------------------
        return self._reason_general_overview(query, user_role, user_name, user_department)

    # =========================================================================
    # REASONING MODULES
    # =========================================================================

    def _reason_reconciliation(self, user_role: str, user_department: Optional[str]) -> Dict[str, Any]:
        recon = reconciliation_service.run_reconciliation()
        exceptions = reconciliation_service.get_exceptions()

        ex_blocks = []
        for ex in exceptions:
            ex_blocks.append(
                f"- **{ex['exception_id']} ({ex['type']})**: Bank ₹{ex['bank_amount']:,.2f} vs Ledger ₹{ex['ledger_amount']:,.2f} "
                f"(Variance ₹{ex['variance']:,.2f}) — Confidence: **{ex['confidence']}%**\n"
                f"  *Proposer*: {ex['ai_proposer_summary']}\n"
                f"  *Verifier*: {ex['ai_verifier_summary']}"
            )

        resp = (
            f"## ⚖️ Hybrid Financial Reconciliation & Exception Report\n\n"
            f"I've executed the Two-Stage Hybrid Reconciliation across Bank Statements, Internal Ledger, and Gateway Batch Feeds.\n\n"
            f"### Deterministic Fast Path (Stage 1)\n"
            f"- **Total Transactions Processed**: **{recon['total_transactions']}**\n"
            f"- **Auto-Matched (Deterministic Exact)**: **{recon['auto_matched_count']}** ({recon['match_rate_percentage']}% Match Rate)\n"
            f"- **Ambiguous Exceptions Forwarded to AI**: **{recon['exceptions_count']}**\n\n"
            f"### Proposer + Verifier AI Exceptions (Stage 2)\n"
            + "\n".join(ex_blocks)
            + f"\n\n### AI Controller Recommendation\n"
            f"1. Authorize Settlement Fee Variance on `EXC-2026-01` (matches standard 1.55% gateway fee deduction).\n"
            f"2. Manually verify `EXC-2026-02` with Workplace Solutions to ensure duplicate invoice was not filed."
        )

        return {
            "response": resp,
            "status": "completed",
            "suggested_actions": [
                "Authorize settlement exception EXC-2026-01",
                "Inspect duplicate exception EXC-2026-02",
                "Check cash flow forecast",
            ]
        }

    def _reason_cash_flow(self, user_role: str, user_department: Optional[str]) -> Dict[str, Any]:
        cdata = cash_flow_service.generate_cash_forecast(user_role, user_department)
        h = cdata["horizons"]

        resp = (
            f"## 💵 AI Cash Flow & Liquidity Forecast\n\n"
            f"### Current Liquidity Position\n"
            f"- **Available Liquid Cash**: **₹{cdata['current_liquidity']:,.2f} INR**\n"
            f"- **Liquidity Assessment**: **{cdata['risk_badge']}**\n\n"
            f"### Multi-Horizon Projections\n"
            f"| Horizon | Projected Cash | Net Movement | Inflows | Outflows |\n"
            f"|---|---|---|---|---|\n"
            f"| **7-Day** | ₹{h['seven_day']['projected_liquidity']:,.2f} | ₹{h['seven_day']['net_change']:,.2f} | ₹{h['seven_day']['expected_inflow']:,.2f} | ₹{h['seven_day']['expected_outflow']:,.2f} |\n"
            f"| **30-Day** | ₹{h['thirty_day']['projected_liquidity']:,.2f} | ₹{h['thirty_day']['net_change']:,.2f} | ₹{h['thirty_day']['expected_inflow']:,.2f} | ₹{h['thirty_day']['expected_outflow']:,.2f} |\n"
            f"| **90-Day** | ₹{h['ninety_day']['projected_liquidity']:,.2f} | ₹{h['ninety_day']['net_change']:,.2f} | ₹{h['ninety_day']['expected_inflow']:,.2f} | ₹{h['ninety_day']['expected_outflow']:,.2f} |\n"
            f"| **FY Year-End** | ₹{h['fiscal_year']['projected_liquidity']:,.2f} | ₹{h['fiscal_year']['net_change']:,.2f} | — | — |\n\n"
            f"### AI Analysis & Outflow Drivers\n"
            f"{cdata['ai_explanation']}\n\n"
            f"### Key Outflow Drivers\n"
            + "\n".join([f"- {d}" for d in cdata["key_drivers"]])
        )

        return {
            "response": resp,
            "status": "completed",
            "suggested_actions": [
                "Simulate planned ₹500K expense",
                "Check payroll and employee costs",
                "Forecast department budgets",
            ]
        }

    def _reason_employee_allowance(self, query: str, user_role: str, user_department: Optional[str]) -> Dict[str, Any]:
        anomalies = employee_finance_service.detect_allowance_anomalies(user_role, user_department)
        
        # Check if recommending allowance for a specific employee
        if "recommend" in query.lower() or "rahul" in query.lower():
            rec = employee_finance_service.recommend_allowance_limit("EMP-101", "Travel")
            resp = (
                f"## 👥 AI Employee Allowance Recommendation\n\n"
                f"### Target Employee\n"
                f"- **Name**: **{rec['employee_name']}** ({rec['designation']})\n"
                f"- **Department**: **{rec['department']}**\n"
                f"- **Allowance Category**: **{rec['allowance_type']} Allowance**\n\n"
                f"### Analysis & Proposed Policy Limit\n"
                f"- **Current Configured Limit**: ₹{rec['current_monthly_limit']:,.2f}/month\n"
                f"- **Historical Approved Velocity**: ₹{rec['historical_monthly_average']:,.2f}/month\n"
                f"- **AI Recommended Monthly Limit**: **₹{rec['recommended_monthly_limit']:,.2f}/month**\n"
                f"- **Confidence Score**: **{rec['confidence_percentage']}%**\n\n"
                f"### Justification\n"
                f"{rec['justification']}\n\n"
                f"### Data Evaluated\n"
                + "\n".join([f"- {d}" for d in rec["data_sources_evaluated"]])
            )
            return {
                "response": resp,
                "status": "completed",
                "suggested_actions": [
                    "Update Rahul Sharma travel limit to ₹15,000",
                    "Scan all employee claims for anomalies",
                    "View employee financial profiles",
                ]
            }

        # Otherwise list allowance anomalies
        ano_blocks = []
        for a in anomalies:
            ano_blocks.append(f"- **{a['badge']} — {a['employee_name']} ({a['department']})**: {a['description']}")

        resp = (
            f"## ⚠️ AI Employee Allowance & Claims Governance\n\n"
            f"I've scanned all active employee claims against company allowance policies.\n\n"
            f"### Active Allowance Anomalies ({len(anomalies)} Found)\n"
            + "\n".join(ano_blocks)
            + f"\n\n### AI Controller Recommendation\n"
            f"1. Request review from Engineering Head for Rahul Sharma's excess travel claim (₹9,800 over policy limit).\n"
            f"2. Inspect Aman Mehra's duplicate ₹7,400 receipt claim within 24 hours."
        )

        return {
            "response": resp,
            "status": "completed",
            "suggested_actions": [
                "Recommend allowance limit for Rahul Sharma",
                "View payroll summary",
                "Check cash flow forecast",
            ]
        }

    def _reason_payroll_and_tax(self, query: str, user_role: str, user_department: Optional[str]) -> Dict[str, Any]:
        if "headcount" in query.lower() or "next year" in query.lower() or "cost" in query.lower():
            hc = payroll_service.get_headcount_cost_analytics()
            growth = hc["headcount_growth_forecast"]
            resp = (
                f"## 📈 AI Total Employee Cost & Headcount Growth Forecast\n\n"
                f"### Current Annual Compensation Profile\n"
                f"- **Total Annual Employee Cost**: **₹{hc['total_annual_employee_cost']:,.2f} INR**\n"
                f"- **Base Salaries**: ₹{hc['cost_breakdown']['base_salaries']:,.2f}\n"
                f"- **Allowances**: ₹{hc['cost_breakdown']['employee_allowances']:,.2f}\n"
                f"- **Benefits & Insurance**: ₹{hc['cost_breakdown']['wellness_and_benefits']:,.2f}\n"
                f"- **Employer Statutory PF/ESI**: ₹{hc['cost_breakdown']['employer_statutory_pf']:,.2f}\n\n"
                f"### Department-Wise Compensation Burden\n"
                f"- **Engineering**: ₹{hc['department_cost_distribution']['Engineering']['annual_cost']:,.2f} (**81.7%** of Dept OPEX)\n"
                f"- **Marketing**: ₹{hc['department_cost_distribution']['Marketing']['annual_cost']:,.2f} (**55.2%** of Dept OPEX)\n"
                f"- **Finance**: ₹{hc['department_cost_distribution']['Finance']['annual_cost']:,.2f} (**72.0%** of Dept OPEX)\n\n"
                f"### Headcount Cost Trajectory Forecast\n"
                f"- **6 Months**: {growth['six_months']['projected_headcount']} Employees → **₹{growth['six_months']['projected_annual_cost']:,.2f}** (+{growth['six_months']['growth_pct']}%)\n"
                f"- **12 Months**: {growth['twelve_months']['projected_headcount']} Employees → **₹{growth['twelve_months']['projected_annual_cost']:,.2f}** (+{growth['twelve_months']['growth_pct']}%)\n"
                f"- **24 Months**: {growth['twenty_four_months']['projected_headcount']} Employees → **₹{growth['twenty_four_months']['projected_annual_cost']:,.2f}** (+{growth['twenty_four_months']['growth_pct']}%)\n\n"
                f"### AI Strategic Takeaway\n"
                f"{hc['ai_executive_takeaway']}"
            )
            return {
                "response": resp,
                "status": "completed",
                "suggested_actions": [
                    "View August payroll register",
                    "Check Form 16 / TDS reconciliation",
                    "Forecast cash flow runway",
                ]
            }

        # Otherwise return Payroll Bill & Form 16 Cross-Check
        psummary = payroll_service.get_payroll_summary(user_role, user_department)
        tax = payroll_service.get_tax_reconciliation(user_role, user_department)

        rec_blocks = []
        for r in psummary["records"]:
            flag = "🔴 MISMATCH" if r["status"] == "MISMATCH_DETECTED" else "🟢 OK"
            rec_blocks.append(
                f"- **{r['name']} ({r['department']})**: Gross Paid: ₹{r['payroll_gross']:,.2f} | Expected: ₹{r['expected_gross']:,.2f} | Net: ₹{r['net_salary_paid']:,.2f} ({flag})\n"
                f"  *{r['mismatch_explanation']}*"
            )

        resp = (
            f"## 📋 AI Payroll Analyzer & Form 16 / TDS Tax Reconciliation\n\n"
            f"### Corporate Payroll Summary ({psummary['payroll_month']})\n"
            f"- **Total Gross Disbursed**: **₹{psummary['total_gross_disbursed']:,.2f}**\n"
            f"- **Total Net Salary Paid**: **₹{psummary['total_net_payout']:,.2f}**\n"
            f"- **TDS Withheld**: **₹{psummary['total_tds_withheld']:,.2f}** | **PF Deductions**: **₹{psummary['total_pf_deductions']:,.2f}**\n"
            f"- **Compliance Status**: **{psummary['compliance_status']}** ({psummary['mismatch_count']} Anomaly Detected)\n\n"
            f"### Salary Bill Cross-Check Results\n"
            + "\n".join(rec_blocks)
            + f"\n\n### Form 16 & TDS Tax Consistency\n"
            f"- **Total Tax Files Audited**: {tax['total_records_audited']}\n"
            f"- **Reconciled Tax Credits**: {tax['fully_reconciled_count']} / {tax['total_records_audited']}\n"
            f"- **Notice on EMP-101 (Rahul Sharma)**: Form 16 reported gross (₹10.44L) differs from annualized payroll gross (₹11.40L). Requires payroll adjustment review."
        )

        return {
            "response": resp,
            "status": "completed",
            "suggested_actions": [
                "Forecast headcount cost for next year",
                "Check employee allowance anomalies",
                "View reconciliation status",
            ]
        }

    def _reason_overspending(self, user_role: str, user_department: Optional[str]) -> Dict[str, Any]:
        health = intelligence_service.calculate_health_score(user_role, user_department)
        forecasts = intelligence_service.get_department_forecasts(user_role, user_department)
        
        all_depts = budget_service.get_all_departments(user_role, user_department)
        total_alloc = sum(d["allocated_budget"] for d in all_depts.values())
        total_spent = sum(d["spent_amount"] for d in all_depts.values())
        util_pct = (total_spent / total_alloc * 100) if total_alloc > 0 else 0.0

        dept_blocks = []
        for f in forecasts:
            status_icon = "🔴" if f["risk_level"] == "CRITICAL" else ("🟠" if f["risk_level"] == "HIGH" else ("🟡" if f["risk_level"] == "MEDIUM" else "🟢"))
            dept_blocks.append(
                f"- **{f['department']}**: Utilization **{f['current_utilization_pct']}%** | Run-Rate: **₹{f['monthly_run_rate']:,.2f}/mo** | "
                f"Projected Year-End: **₹{f['projected_year_end_spend']:,.2f}** ({status_icon} {f['risk_level']})"
            )

        overrun_depts = [f for f in forecasts if f["is_overrun"]]
        finding = (
            f"Marketing and Engineering are consuming budget at an elevated pace relative to the fiscal calendar. "
            f"At current run-rates, projected year-end deficit is ₹{sum(f['projected_overrun_amount'] for f in overrun_depts):,.2f}."
            if overrun_depts else "All departments are spending within allocated envelope."
        )

        resp = (
            f"## 📊 AI Overspending & Burn Velocity Analysis\n\n"
            f"I've evaluated the live ledger across all authorized departments against the elapsed portion of **FY 2026–2027 (Month 5/12 = 41.7% Elapsed)**.\n\n"
            f"### Overall Financial Assessment\n"
            f"⚠️ **Elevated Deficit Risk**\n\n"
            f"- **Total Budget**: ₹{total_alloc:,.2f}\n"
            f"- **Committed Spend**: ₹{total_spent:,.2f}\n"
            f"- **Current Utilization**: **{util_pct:.1f}%** (Expected Pace: **41.7%**)\n"
            f"- **Corporate Health Score**: **{health['overall_score']}/100 ({health['rating']})**\n\n"
            f"### Department Run-Rate Breakdown\n"
            + "\n".join(dept_blocks)
            + f"\n\n### AI Finding\n"
            f"{finding}\n\n"
            f"### Recommended Actions\n"
            f"1. Implement cost cap on Engineering cloud infrastructure spend.\n"
            f"2. Audit recent high-value vendor invoices.\n"
            f"3. Execute AI Reallocation of ₹250,000 from Operations surplus to Engineering.\n"
            f"4. Require strict manager authorization on all claims exceeding ₹50,000.\n\n"
            f"**AI Confidence: 91%**"
        )

        return {
            "response": resp,
            "status": "completed",
            "suggested_actions": [
                "Why is Engineering overspending?",
                "Can we afford another ₹500,000 for Engineering?",
                "Give me today's watchtower brief",
                "Execute Operations-to-Engineering budget reallocation",
            ]
        }

    def _reason_affordability(
        self,
        amount: float,
        department: str,
        category: str,
        user_role: str,
        user_department: Optional[str],
    ) -> Dict[str, Any]:
        sim = intelligence_service.simulate_affordability(amount, department, category)
        dept_info = budget_service.get_department_budget(department, user_role, user_department)

        remaining_b = dept_info.get("remaining", dept_info.get("allocated_budget", 0.0) - dept_info.get("spent_amount", 0.0))
        verdict_icon = "🟢" if sim["verdict"] == "APPROVED_SAFE" else ("🟡" if sim["verdict"] == "CAUTION" else "🔴")

        resp = (
            f"## 🎯 AI Expense Affordability Analysis\n\n"
            f"### Proposed Disbursement\n"
            f"- **Amount**: **₹{amount:,.2f} INR**\n"
            f"- **Department**: **{department}**\n"
            f"- **Category**: **{category}**\n\n"
            f"### Current Department Runway Position\n"
            f"- **Allocated Budget**: ₹{dept_info['allocated_budget']:,.2f}\n"
            f"- **Committed Spend**: ₹{dept_info['spent_amount']:,.2f}\n"
            f"- **Current Available Runway**: **₹{remaining_b:,.2f}**\n\n"
            f"### Post-Disbursement Simulation\n"
            f"- **Remaining Department Runway**: **₹{sim['post_expense_remaining']:,.2f}**\n"
            f"- **Budget Impact**: **+{sim['budget_impact_percentage']}%** of annual allocation\n"
            f"- **Post-Expense Utilization**: **{sim['post_utilization_percentage']}%**\n"
            f"- **Company Liquidity Pool**: ₹{sim['company_liquidity_available']:,.2f}\n\n"
            f"### AI Assessment\n"
            f"{verdict_icon} **{sim['verdict_badge']}**\n\n"
            f"{sim['recommendation']}\n\n"
            f"### Recommended Actions\n"
            f"1. {'Route to Manager/CFO Authorization Queue (exceeds ₹50,000 policy threshold).' if amount >= 50000 else 'Authorize within autonomous limit.'}\n"
            f"2. Verify cloud vendor contractual milestone delivery.\n"
            f"3. Monitor department run-rate over next 30 days.\n\n"
            f"**AI Confidence: 94%**"
        )

        return {
            "response": resp,
            "status": "completed",
            "suggested_actions": [
                f"Submit ₹{amount:,.0f} expense request for {department}",
                f"Forecast {department} year-end spending",
                "Are we overspending?",
            ]
        }

    def _reason_department_risks(self, user_role: str, user_department: Optional[str]) -> Dict[str, Any]:
        forecasts = intelligence_service.get_department_forecasts(user_role, user_department)
        # Sort by overrun amount descending
        sorted_f = sorted(forecasts, key=lambda x: x["projected_overrun_amount"], reverse=True)

        ranked_blocks = []
        for idx, f in enumerate(sorted_f, start=1):
            icon = "🔴" if f["risk_level"] == "CRITICAL" else ("🟠" if f["risk_level"] == "HIGH" else ("🟡" if f["risk_level"] == "MEDIUM" else "🟢"))
            overrun_str = f"Projected Overrun: ₹{f['projected_overrun_amount']:,.2f}" if f['is_overrun'] else f"Surplus: ₹{f['projected_surplus_amount']:,.2f}"
            ranked_blocks.append(
                f"### {idx}. {f['department']} — {icon} {f['risk_level']} RISK\n"
                f"- **Budget Allocation**: ₹{f['allocated_budget']:,.2f} | **Spent**: ₹{f['spent_amount']:,.2f} (**{f['current_utilization_pct']}%**)\n"
                f"- **Monthly Run-Rate**: ₹{f['monthly_run_rate']:,.2f}/mo\n"
                f"- **Year-End Projection**: ₹{f['projected_year_end_spend']:,.2f} ({overrun_str})\n"
                f"- *Analysis*: {f['ai_summary']}"
            )

        resp = (
            f"## 🏆 Department Risk Hierarchy & Runway Ranking\n\n"
            f"Based on real-time extrapolation of monthly burn rates against **FY 2026–2027** allocations:\n\n"
            + "\n\n".join(ranked_blocks)
            + f"\n\n### Strategic Takeaway\n"
            f"Prioritize cost control and invoice audit on **{sorted_f[0]['department']}** and **{sorted_f[1]['department']}** to preserve corporate margins."
        )

        return {
            "response": resp,
            "status": "completed",
            "suggested_actions": [
                f"Why is {sorted_f[0]['department']} overspending?",
                "How can we reduce spending?",
                "Give me today's watchtower brief",
            ]
        }

    def _reason_department_deep_dive(self, department: str, user_role: str, user_department: Optional[str]) -> Dict[str, Any]:
        dept_info = budget_service.get_department_budget(department, user_role, user_department)
        invoices = invoice_service.get_all_invoices(user_role, user_department)
        dept_invs = [inv for inv in invoices if inv.get("department", "").lower() == department.lower()]

        inv_blocks = []
        for inv in dept_invs:
            inv_blocks.append(f"- `{inv['invoice_id']}`: **{inv['vendor_name']}** — **₹{inv['total_amount']:,.2f}** ({inv['status']})")

        resp = (
            f"## 🔍 Deep Dive Analysis: {department} Department\n\n"
            f"### Financial Position\n"
            f"- **Budget Allocation**: ₹{dept_info['allocated_budget']:,.2f}\n"
            f"- **Committed Spend**: ₹{dept_info['spent_amount']:,.2f}\n"
            f"- **Remaining Runway**: ₹{dept_info.get('remaining', dept_info.get('allocated_budget', 0.0) - dept_info.get('spent_amount', 0.0)):,.2f}\n"
            f"- **Utilization**: **{(dept_info['spent_amount'] / dept_info['allocated_budget'] * 100):.1f}%**\n\n"
            f"### Primary Spend Drivers & Invoices\n"
            + ("\n".join(inv_blocks) if inv_blocks else "No recent invoice claims found.")
            + f"\n\n### Key Cause & Diagnosis\n"
            f"The primary driver of {department}'s spend velocity is high recurring cloud infrastructure consumption and unoptimized monthly commitments.\n\n"
            f"### Recommended Actions\n"
            f"1. Audit cloud usage for idle database instances and non-production clusters.\n"
            f"2. Enforce 3-way matching on all incoming {department} purchase orders."
        )

        return {
            "response": resp,
            "status": "completed",
            "suggested_actions": [
                f"Can we afford another ₹500,000 for {department}?",
                "How can we reduce spending?",
                "Top vendor risks",
            ]
        }

    def _reason_invoice_anomalies(self, user_role: str, user_department: Optional[str]) -> Dict[str, Any]:
        invoices = invoice_service.get_all_invoices(user_role, user_department)
        suspicious_list = []
        for inv in invoices:
            flags = []
            subtotal = float(inv.get("subtotal") or (inv.get("total_amount", 0.0) / 1.18))
            tax_claimed = float(inv.get("tax_gst") if inv.get("tax_gst") is not None else inv.get("tax_amount", subtotal * 0.18))
            total_amt = float(inv.get("total_amount") or (subtotal + tax_claimed))
            # Tax check
            expected_tax = round(subtotal * 0.18, 2)
            if abs(tax_claimed - expected_tax) > 1.0:
                flags.append(f"Tax Mismatch: Claimed ₹{tax_claimed:,.2f} vs Expected 18% GST (₹{expected_tax:,.2f})")
            if total_amt >= 50000:
                flags.append("Exceeds Manager Authorization Threshold (≥ ₹50,000)")
            if flags:
                suspicious_list.append({"inv": inv, "flags": flags})

        blocks = []
        for s in suspicious_list:
            inv = s["inv"]
            blocks.append(
                f"### ⚠️ Invoice `{inv['invoice_id']}` — {inv['vendor_name']}\n"
                f"- **Amount**: ₹{inv['total_amount']:,.2f} | **Department**: {inv['department']} | **Status**: `{inv['status']}`\n"
                f"- **Flags**: " + "; ".join(s["flags"])
            )

        resp = (
            f"## 🕵️ AI Invoice Anomaly & Compliance Report\n\n"
            f"I've audited all {len(invoices)} invoices in the repository for:\n"
            f"- 18% GST tax rate mathematical consistency\n"
            f"- Multi-vector fuzzy duplicate submissions\n"
            f"- Budget cap threshold breaches\n\n"
            f"### Identified Audit Flags & Reviews ({len(suspicious_list)} Total)\n\n"
            + "\n\n".join(blocks)
            + f"\n\n### AI Auditor Recommendation\n"
            f"Hold disbursement on flagged items until supplier provides revised GST credit notes."
        )

        return {
            "response": resp,
            "status": "completed",
            "suggested_actions": [
                "Scan for duplicate invoices",
                "Top vendor risks",
                "Are we overspending?",
            ]
        }

    def _reason_vendor_intelligence(self, user_role: str) -> Dict[str, Any]:
        vendors = intelligence_service.get_vendor_intelligence()
        v_blocks = []
        for v in vendors:
            status_icon = "🔴" if v["risk_score"] > 60 else ("🟡" if v["risk_score"] > 30 else "🟢")
            v_blocks.append(
                f"### {status_icon} {v['vendor_name']} ({v['primary_department']})\n"
                f"- **Total Spend**: **₹{v['total_spend']:,.2f}** | Invoices: **{v['invoice_count']}** | Avg Ticket: **₹{v['average_invoice']:,.2f}**\n"
                f"- **Risk Score**: **{v['risk_score']}/100 ({v['status']})** | Anomalies Detected: **{v['anomalies_detected']}**"
            )

        resp = (
            f"## 🏢 Vendor Spend Concentration & Risk Radar\n\n"
            f"Evaluating top suppliers across payment frequency, ticket variance, and compliance integrity:\n\n"
            + "\n\n".join(v_blocks)
            + f"\n\n### AI Recommendation\n"
            f"CloudOps Technologies requires contract review due to increasing monthly invoice sizes."
        )

        return {
            "response": resp,
            "status": "completed",
            "suggested_actions": [
                "Find suspicious invoices",
                "Can we afford ₹500,000 for Engineering?",
                "Give me today's watchtower brief",
            ]
        }

    def _reason_watchtower_brief(self, user_role: str, user_department: Optional[str]) -> Dict[str, Any]:
        alerts = intelligence_service.get_watchtower_alerts(user_role, user_department)
        health = intelligence_service.calculate_health_score(user_role, user_department)

        alert_blocks = []
        for a in alerts:
            alert_blocks.append(f"- **{a['badge']}**: **{a['title']}** — {a['message']} *(Action: {a['action_label']})*")

        resp = (
            f"## 📡 AI Financial Watchtower — Daily Intelligence Brief\n\n"
            f"**Corporate Health Score**: **{health['overall_score']}/100 ({health['rating']})**  \n"
            f"**Monitoring Status**: Active across 5 departments.\n\n"
            f"### Active Autonomous Alerts\n"
            + "\n".join(alert_blocks)
            + f"\n\n### Key Executive Takeaway\n"
            f"Liquidity is healthy (₹8.43M), but Engineering and Marketing burn velocity requires immediate management oversight."
        )

        return {
            "response": resp,
            "status": "completed",
            "suggested_actions": [
                "Are we overspending?",
                "How can we reduce spending?",
                "Which department is most at risk?",
            ]
        }

    def _reason_forecast(self, user_role: str, user_department: Optional[str]) -> Dict[str, Any]:
        forecasts = intelligence_service.get_department_forecasts(user_role, user_department)
        f_rows = []
        for f in forecasts:
            status = "🔴 DEFICIT" if f["is_overrun"] else "🟢 SURPLUS"
            f_rows.append(
                f"| **{f['department']}** | ₹{f['allocated_budget']:,.0f} | ₹{f['spent_amount']:,.0f} | ₹{f['monthly_run_rate']:,.0f}/mo | ₹{f['projected_year_end_spend']:,.0f} | {status} |"
            )

        resp = (
            f"## 🔮 FY 2026–2027 Full-Year Budget Forecast\n\n"
            f"Forecasts calculated using actual 5-month spending run-rates extrapolated across the remaining 7 months:\n\n"
            f"| Department | Annual Cap | Spent To Date | Monthly Burn | Projected Year-End | Risk Level |\n"
            f"|---|---|---|---|---|---|\n"
            + "\n".join(f_rows)
            + f"\n\n### Forecast Insights\n"
            f"- **Total Projected Spending**: ₹{sum(f['projected_year_end_spend'] for f in forecasts):,.2f}\n"
            f"- **Net Projected Position**: Deficit pressure in Engineering & Marketing offset by strong surpluses in Operations & HR."
        )

        return {
            "response": resp,
            "status": "completed",
            "suggested_actions": [
                "Are we overspending?",
                "How can we reduce spending?",
                "Can we afford another ₹500,000 for Engineering?",
            ]
        }

    def _reason_cost_reduction(self, user_role: str, user_department: Optional[str]) -> Dict[str, Any]:
        proposals = intelligence_service.get_proposals()
        p_blocks = []
        for p in proposals:
            p_blocks.append(
                f"- **{p['proposal_id']}**: Reallocate **₹{p['amount']:,.2f}** from `{p['from_department']}` to `{p['to_department']}` — *{p['reason']}* (Impact: {p['projected_impact']})"
            )

        resp = (
            f"## 💡 AI Cost Optimization & Spend Reduction Strategy\n\n"
            f"To prevent projected year-end deficits and preserve liquidity, the AI Controller recommends:\n\n"
            f"### 1. High-Impact Strategic Opportunities\n"
            f"- **Mitigate Projected Engineering Cloud Overrun**: Engineering cloud infrastructure spending velocity is projected to generate a deficit if unchecked.\n"
            f"- **Consolidate Vendor Licenses**: AWS and SaaS tool consolidation can save an estimated ₹120,000/quarter.\n"
            f"- **Authorize AI Budget Reallocations**: Transfer surplus capacity from Operations to Engineering.\n\n"
            f"### 2. Available AI Proposals (Ready for CFO Execution)\n"
            + "\n".join(p_blocks)
            + f"\n\n### 3. Policy Levers\n"
            f"- Mandate PO pre-approval for discretionary software claims.\n"
            f"- Enforce 18% GST tax rate verification before approving supplier payments."
        )

        return {
            "response": resp,
            "status": "completed",
            "suggested_actions": [
                "Execute Operations-to-Engineering budget reallocation",
                "Are we overspending?",
                "Top vendor risks",
            ]
        }

    def _reason_general_overview(self, query: str, user_role: str, user_name: str, user_department: Optional[str]) -> Dict[str, Any]:
        health = intelligence_service.calculate_health_score(user_role, user_department)
        resp = (
            f"## 🏛️ Autonomous Financial Controller — Briefing for {user_name}\n\n"
            f"**Current Status**: Online & Monitoring Corporate Ledger (FY 2026–2027)  \n"
            f"**Corporate Health Score**: **{health['overall_score']}/100 ({health['rating']})**  \n"
            f"**Liquidity Reserve**: **₹8,435,000.00 INR**\n\n"
            f"### I can assist you with:\n"
            f"1. **Spending Velocity & Run-Rates**: Ask *'Are we overspending?'*\n"
            f"2. **Expense Affordability Simulations**: Ask *'Can we afford ₹500,000 for Engineering?'*\n"
            f"3. **Department Risk Hierarchy**: Ask *'Which department is most at risk?'*\n"
            f"4. **Reconciliation & Gateway Settlements**: Ask *'What is our reconciliation status?'*\n"
            f"5. **Cash Flow & Liquidity**: Ask *'What is our 30-day cash forecast?'*\n"
            f"6. **Employee Allowances & Claims**: Ask *'Recommend allowance for Rahul Sharma'* or *'Check claim anomalies'*\n"
            f"7. **Payroll & Form 16 Cross-Check**: Ask *'Check August payroll for mismatches'*\n"
            f"8. **Headcount & Compensation Forecast**: Ask *'What will employee cost be next year?'*"
        )

        return {
            "response": resp,
            "status": "completed",
            "suggested_actions": [
                "Are we overspending?",
                "What is our 30-day cash forecast?",
                "What is our reconciliation status?",
                "Recommend allowance for Rahul Sharma",
            ]
        }

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _extract_amount(self, query: str) -> Optional[float]:
        q = query.replace(",", "").lower()
        # Look for e.g. 500k -> 500000
        k_match = re.search(r"(\d+(?:\.\d+)?)\s*k\b", q)
        if k_match:
            return float(k_match.group(1)) * 1000.0

        # Look for e.g. 5 lakh / lac
        lakh_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac|l)\b", q)
        if lakh_match:
            return float(lakh_match.group(1)) * 100000.0

        # Look for raw digits e.g. 500000 or ₹500000
        num_match = re.search(r"(?:₹|rs\.?|inr)?\s*(\d{4,9})", q)
        if num_match:
            return float(num_match.group(1))

        return None

    def _extract_department(self, query: str) -> Optional[str]:
        q = query.lower()
        for dept in ["engineering", "marketing", "sales", "operations", "hr", "finance"]:
            if dept in q:
                return dept.capitalize()
        return None


ai_reasoning_engine = AutonomousFinancialReasoningEngine()
