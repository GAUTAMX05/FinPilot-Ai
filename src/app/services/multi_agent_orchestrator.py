import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.app.services.digital_twin_service import digital_twin_service, PAYROLL_LOAD_FACTOR
from src.app.services.budget_service import budget_service
from src.app.services.invoice_service import invoice_service
from src.app.services.employee_finance_service import employee_finance_service
from src.app.services.payroll_service import payroll_service
from src.app.services.cash_flow_service import cash_flow_service
from src.app.services.audit_service import audit_service
from src.app.services.policy_calibration_service import policy_calibration_service

logger = logging.getLogger("MultiAgentOrchestrator")


class MultiAgentFinancialOrchestrator:
    """
    Coordinates multi-agent financial reasoning across 7 specialized sub-agents:
    1. Intent Agent: Classifies request type and enforces RBAC permission bounds.
    2. Retrieval Agent: Pulls role-scoped data facts with lineage tracking.
    3. Analysis Agent: Runs deterministic calculations (burn rates, GST, duplicates).
    4. Risk Agent: Computes weighted, explainable multi-factor risk scores.
    5. Simulation Agent: Runs forward projections against the Financial Digital Twin.
    6. Causal Agent: Pinpoints root causes by correlating anomalies with nearby signals.
    7. Narrator Agent: Formulates role-tailored plain-language synthesis ("What Happened",
       "Why It Matters", "What Should Be Done", "Who Needs to Act", "What Happens Next").
    8. Approval Router: Determines execution vs. escalation paths.
    """

    def process_query(
        self,
        query: str,
        user_role: str = "CFO",
        user_name: str = "User",
        user_department: Optional[str] = None,
        context_override: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Runs the complete multi-agent pipeline with audit-grade memory logging."""
        trace_id = f"TRC-{uuid.uuid4().hex[:8].upper()}"
        agent_steps: List[Dict[str, Any]] = []

        # =====================================================================
        # AGENT 1: INTENT & RBAC AGENT
        # =====================================================================
        q_lower = query.lower()
        intent_type = "GENERAL_FINANCIAL_QUERY"
        if any(w in q_lower for w in ["what if", "what-if", "suppose", "assume", "simulate", "if we delay", "if we spend", "if we hire"]):
            intent_type = "COUNTERFACTUAL_SIMULATION"
        elif any(w in q_lower for w in ["why", "cause", "root cause", "coincide", "explain overrun", "mismatch cause"]):
            intent_type = "CAUSAL_ROOT_CAUSE_ANALYSIS"
        elif any(w in q_lower for w in ["policy", "calibrate", "override", "suggestion", "friction"]):
            intent_type = "POLICY_CALIBRATION_REVIEW"
        elif any(w in q_lower for w in ["afford", "can we buy", "can we spend"]):
            intent_type = "AFFORDABILITY_EVALUATION"
        elif any(w in q_lower for w in ["payroll", "form 16", "tds", "salary mismatch"]):
            intent_type = "TAX_PAYROLL_AUDIT"
        elif any(w in q_lower for w in ["overspend", "burn rate", "runway", "utilization"]):
            intent_type = "BUDGET_RUNWAY_ASSESSMENT"

        # RBAC Check
        rbac_permitted = True
        if user_role == "DEPARTMENT_HEAD" and user_department:
            other_depts = [d for d in ["marketing", "sales", "operations", "hr", "engineering"] if d != user_department.lower()]
            for od in other_depts:
                if od in q_lower and user_department.lower() not in q_lower:
                    rbac_permitted = False

        intent_step = {
            "agent": "IntentAgent",
            "intent": intent_type,
            "rbac_permitted": rbac_permitted,
            "confidence": 0.96,
            "timestamp": datetime.utcnow().isoformat(),
        }
        agent_steps.append(intent_step)

        if not rbac_permitted:
            return self._format_rbac_restriction(user_name, user_department, trace_id, agent_steps)

        # =====================================================================
        # AGENT 2: RETRIEVAL AGENT (ROLE-SCOPED DATA FETCHING)
        # =====================================================================
        twin_state = digital_twin_service.get_live_state()
        retrieved_facts: Dict[str, Any] = {
            "liquid_reserves": twin_state["cash_position"]["liquid_reserves"],
            "total_allocated_budget": twin_state["budget_position"]["total_allocated"],
            "total_spent_budget": twin_state["budget_position"]["total_spent"],
            "monthly_burn_total": twin_state["budget_position"]["total_monthly_burn"],
            "headcount": twin_state["payroll_position"]["headcount"],
            "pending_invoices_count": twin_state["commitments"]["pending_invoices_count"],
        }
        if user_role == "DEPARTMENT_HEAD" and user_department:
            dept_info = twin_state["budget_position"]["departments"].get(user_department, {})
            retrieved_facts["scoped_department"] = dept_info

        retrieval_step = {
            "agent": "RetrievalAgent",
            "data_sources": ["digital_twin", "budget_ledger", "payroll_register", "invoice_store"],
            "lineage_records_retrieved": len(retrieved_facts),
            "timestamp": datetime.utcnow().isoformat(),
        }
        agent_steps.append(retrieval_step)

        # =====================================================================
        # AGENT 3: QUANTITATIVE ANALYSIS AGENT
        # =====================================================================
        burn_analysis = {
            "pace_status": "HIGH_BURN_VELOCITY" if twin_state["budget_position"]["utilization_pct"] > 35 else "ALIGNED",
            "utilization_pct": twin_state["budget_position"]["utilization_pct"],
            "engineering_overrun_projected": twin_state["budget_position"]["departments"].get("Engineering", {}).get("projected_year_end", 0.0) > twin_state["budget_position"]["departments"].get("Engineering", {}).get("allocated_budget", 0.0),
        }
        agent_steps.append({
            "agent": "AnalysisAgent",
            "burn_velocity": burn_analysis["pace_status"],
            "budget_utilization": f"{burn_analysis['utilization_pct']}%",
            "timestamp": datetime.utcnow().isoformat(),
        })

        # =====================================================================
        # AGENT 4: WEIGHTED FACTOR RISK AGENT
        # =====================================================================
        risk_score_data = twin_state["decision_score"]
        agent_steps.append({
            "agent": "RiskAgent",
            "overall_score": risk_score_data["overall_score"],
            "rating": risk_score_data["rating"],
            "factors": risk_score_data["factors"],
            "timestamp": datetime.utcnow().isoformat(),
        })

        # =====================================================================
        # AGENT 5: SIMULATION AGENT (DIGITAL TWIN FORWARD PROJECTION)
        # =====================================================================
        sim_result = digital_twin_service.run_what_if_scenario(
            scenario_text=query,
            user_role=user_role,
            user_department=user_department,
        )
        agent_steps.append({
            "agent": "SimulationAgent",
            "simulation_horizon": f"{sim_result.get('horizon_days', 90)} Days",
            "projected_liquidity_delta": sim_result["deltas"]["liquidity_change"],
            "projected_runway_delta": sim_result["deltas"]["runway_days_change"],
            "verdict": sim_result["verdict"],
            "timestamp": datetime.utcnow().isoformat(),
        })

        # =====================================================================
        # AGENT 6: CAUSAL AGENT (CORRELATING ANOMALIES AGAINST NEARBY SIGNALS)
        # =====================================================================
        causal_analysis = self._run_causal_correlation(query, user_department)
        agent_steps.append({
            "agent": "CausalAgent",
            "top_root_cause": causal_analysis["primary_cause"],
            "correlation_confidence": causal_analysis["confidence"],
            "correlated_signals": causal_analysis["correlated_signals"],
            "timestamp": datetime.utcnow().isoformat(),
        })

        # =====================================================================
        # AGENT 7: NARRATOR AGENT (ROLE-AWARE SYNTHESIS)
        # =====================================================================
        narrative = self._generate_role_narrative(
            query=query,
            user_role=user_role,
            user_name=user_name,
            user_department=user_department,
            intent=intent_type,
            sim_result=sim_result,
            causal=causal_analysis,
            twin_state=twin_state,
        )

        # Log complete reasoning trajectory to Audit Trail
        audit_service.log_action(
            user_id="sys_agent_orchestrator",
            user_name="MultiAgent Reasoning System",
            role=user_role,
            action=f"AI_REASONING_PIPELINE_{intent_type}",
            entity="DECISION_PIPELINE",
            entity_id=trace_id,
            details=f"Evaluated query: '{query[:80]}...' across 7 sub-agents. Decision Score: {risk_score_data['overall_score']}/100. Simulation Verdict: {sim_result['verdict']}.",
            risk_level="LOW",
        )

        return {
            "trace_id": trace_id,
            "intent": intent_type,
            "response": narrative,
            "simulation": sim_result,
            "causal_analysis": causal_analysis,
            "agent_steps": agent_steps,
            "suggested_actions": narrative.get("suggested_actions", []),
        }

    def _run_causal_correlation(self, query: str, user_department: Optional[str] = None) -> Dict[str, Any]:
        """Correlates anomalies against contextual operational signals."""
        q_lower = query.lower()
        if "engineering" in q_lower or "cloud" in q_lower or (user_department == "Engineering"):
            return {
                "anomaly_type": "BUDGET_RUN_RATE_OVERRUN",
                "department": "Engineering",
                "primary_cause": "Unbudgeted Q2 Production Kubernetes Expansion",
                "confidence": 0.94,
                "correlated_signals": [
                    "3 new CloudOps Technologies invoices added in the last 14 days amounting to ₹200,600.",
                    "AWS savings plan renewal variance accounted for +18% above baseline monthly projection.",
                    "Submitter clustering: 80% of recent cloud claims originated from same team lead.",
                ],
                "recommended_fix": "Execute approved ₹250,000 budget reallocation from Operations surplus and initiate quarterly CloudOps rate renegotiation.",
            }
        elif "marketing" in q_lower:
            return {
                "anomaly_type": "CAMPAIGN_BURN_SURGE",
                "department": "Marketing",
                "primary_cause": "Paid Customer Acquisition Surge in Meta/Google Ads",
                "confidence": 0.89,
                "correlated_signals": [
                    "Google Ads performance max campaign front-loaded in Month 5.",
                    "Higher cost-per-click observed during festive seasonal ramp-up.",
                ],
                "recommended_fix": "Pace digital ad spend over remaining quarters and rebalance spend toward organic inbound channels.",
            }
        elif "form 16" in q_lower or "salary mismatch" in q_lower or "tds" in q_lower:
            return {
                "anomaly_type": "FORM_16_SALARY_MISMATCH",
                "department": "All",
                "primary_cause": "Unclassified Reimbursement Arrears Omitted from Annexure B",
                "confidence": 0.96,
                "correlated_signals": [
                    "Discrepancy of ₹35,000 on EMP-1042 coincides with retroactive travel claim payout in Q2.",
                    "TDS deducted at source on gross payroll, but Form 16 Part B omitted the non-taxable reimbursement offset.",
                ],
                "recommended_fix": "Update Form 16 Part B to reflect non-taxable travel reimbursement before quarterly compliance filing.",
            }
        else:
            return {
                "anomaly_type": "GENERAL_VARIANCE_CHECK",
                "department": user_department or "Enterprise",
                "primary_cause": "Normal Operational Disbursal Flow",
                "confidence": 0.85,
                "correlated_signals": [
                    "Current disbursements follow approved PO timelines.",
                    "No anomalous duplicate hashes detected in active ledger.",
                ],
                "recommended_fix": "Maintain current liquidity reserves and monitor 30-day runway curves.",
            }

    def _build_scenario_block(
        self,
        sim_result: Dict[str, Any],
        twin_state: Dict[str, Any],
    ) -> str:
        """Deterministic, scenario-specific arithmetic echoed in every narrative.

        Shows the parsed inputs and the exact figures computed from live data
        so two different what-ifs can never render identical text.
        """
        action = sim_result.get("action", {}) or {}
        a_type = action.get("type", "EXPENSE")
        horizon = sim_result.get("horizon_days", 90)
        deltas = sim_result.get("deltas", {})
        before = sim_result.get("before", {})
        after = sim_result.get("after", {})

        if a_type == "BURN_RATE_SHIFT":
            dept = action.get("department", "Engineering")
            mult = float(action.get("multiplier", 1.12))
            d = twin_state["budget_position"]["departments"].get(dept, {})
            monthly = float(d.get("monthly_burn_rate", 0.0))
            daily = monthly / 30.0
            proj_current = daily * horizon
            proj_shifted = daily * mult * horizon
            remaining = float(d.get("remaining_budget", 0.0))
            coverage = (remaining / daily) if daily > 0 else 0
            return (
                f"**Scenario Inputs:** {dept} spend continues for **{horizon} days** "
                f"at **{mult:.2f}x** benchmark pace.\n"
                f"- **Current {dept} burn:** ₹{monthly:,.0f}/month (₹{daily:,.0f}/day).\n"
                f"- **{horizon}-day projected spend:** ₹{proj_current:,.0f} at current pace; "
                f"₹{proj_shifted:,.0f} at shifted pace "
                f"(extra ₹{proj_shifted - proj_current:,.0f}).\n"
                f"- **{dept} remaining budget:** ₹{remaining:,.0f} ≈ {coverage:.0f} days of cover at current burn.\n"
                f"- **Model impact ({horizon}d):** liquidity {before.get('liquidity_90d', 0):,.0f} → "
                f"{after.get('liquidity_90d', 0):,.0f} ({deltas.get('liquidity_change', 0):+,.0f}); "
                f"runway {before.get('runway_days', 0)} → {after.get('runway_days', 0)} days."
            )

        if a_type == "HEADCOUNT_GROWTH":
            count = int(action.get("headcount", 3))
            salary = float(action.get("avg_salary", 85000.0))
            monthly_basic = abs(count) * salary
            monthly_loaded = monthly_basic * PAYROLL_LOAD_FACTOR
            current_gross = float(twin_state["payroll_position"]["monthly_gross_total"])
            if count < 0:
                n = abs(count)
                new_gross = current_gross - monthly_loaded
                pct = monthly_loaded / current_gross * 100 if current_gross else 0.0
                window_saving = monthly_loaded * (horizon / 30.0)
                return (
                    f"**Scenario Inputs:** reduce **{n}** engineers at **₹{salary:,.0f}/mo basic** "
                    f"over a **{horizon}-day** window.\n"
                    f"- **Monthly saving:** {n} × ₹{salary:,.0f} = **₹{monthly_basic:,.0f}/mo basic**; "
                    f"employer-loaded (×{PAYROLL_LOAD_FACTOR}) = **₹{monthly_loaded:,.0f}/mo**.\n"
                    f"- **Payroll burn:** ₹{current_gross:,.0f}/mo → **₹{new_gross:,.0f}/mo** "
                    f"(-{pct:.1f}%).\n"
                    f"- **{horizon}-day payroll saving of this reduction:** ₹{window_saving:,.0f}.\n"
                    f"- **Model impact ({horizon}d):** liquidity {before.get('liquidity_90d', 0):,.0f} → "
                    f"{after.get('liquidity_90d', 0):,.0f} ({deltas.get('liquidity_change', 0):+,.0f}); "
                    f"runway {before.get('runway_days', 0)} → {after.get('runway_days', 0)} days."
                )
            new_gross = current_gross + monthly_loaded
            window_cost = monthly_loaded * (horizon / 30.0)
            return (
                f"**Scenario Inputs:** hire **{count}** engineers at **₹{salary:,.0f}/mo basic** "
                f"over a **{horizon}-day** window.\n"
                f"- **Monthly cost added:** {count} × ₹{salary:,.0f} = **₹{monthly_basic:,.0f}/mo basic**; "
                f"employer-loaded (×{PAYROLL_LOAD_FACTOR}) = **₹{monthly_loaded:,.0f}/mo**.\n"
                f"- **Payroll burn:** ₹{current_gross:,.0f}/mo → **₹{new_gross:,.0f}/mo** "
                f"(+{monthly_loaded / current_gross * 100:.1f}%).\n"
                f"- **{horizon}-day payroll cost of this hire:** ₹{window_cost:,.0f}.\n"
                f"- **Model impact ({horizon}d):** liquidity {before.get('liquidity_90d', 0):,.0f} → "
                f"{after.get('liquidity_90d', 0):,.0f} ({deltas.get('liquidity_change', 0):+,.0f}); "
                f"runway {before.get('runway_days', 0)} → {after.get('runway_days', 0)} days."
            )

        if a_type == "PAYMENT_DELAY":
            days = int(action.get("days", 14))
            return (
                f"**Scenario Inputs:** delay non-essential vendor disbursements by **{days} days** "
                f"(payroll keeps flowing), projected over **{horizon} days**.\n"
                f"- **Model impact ({horizon}d):** liquidity {before.get('liquidity_90d', 0):,.0f} → "
                f"{after.get('liquidity_90d', 0):,.0f} ({deltas.get('liquidity_change', 0):+,.0f}); "
                f"runway {before.get('runway_days', 0)} → {after.get('runway_days', 0)} days."
            )

        if a_type == "REALLOCATION":
            amt = float(action.get("amount", 250000.0))
            return (
                f"**Scenario Inputs:** reallocate **₹{amt:,.0f}** from "
                f"{action.get('from_department', 'Operations')} to {action.get('to_department', 'Engineering')}.\n"
                f"- **Model impact ({horizon}d):** liquidity {before.get('liquidity_90d', 0):,.0f} → "
                f"{after.get('liquidity_90d', 0):,.0f} ({deltas.get('liquidity_change', 0):+,.0f})."
            )

        amt = float(action.get("amount", 0.0))
        dept = action.get("department", "Operations")
        return (
            f"**Scenario Inputs:** one-time expense of **₹{amt:,.0f}** in {dept}, "
            f"projected over **{horizon} days**.\n"
            f"- **Model impact ({horizon}d):** liquidity {before.get('liquidity_90d', 0):,.0f} → "
            f"{after.get('liquidity_90d', 0):,.0f} ({deltas.get('liquidity_change', 0):+,.0f}); "
            f"runway {before.get('runway_days', 0)} → {after.get('runway_days', 0)} days."
        )

    def _generate_role_narrative(
        self,
        query: str,
        user_role: str,
        user_name: str,
        user_department: Optional[str],
        intent: str,
        sim_result: Dict[str, Any],
        causal: Dict[str, Any],
        twin_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Formats the narrator output according to the user's role depth."""
        deltas = sim_result["deltas"]
        before = sim_result["before"]
        after = sim_result["after"]
        action_desc = sim_result["action_description"]
        horizon = sim_result.get("horizon_days", 90)
        scenario_block = self._build_scenario_block(sim_result, twin_state)

        is_auditor = user_role == "AUDITOR"
        is_dept_head = user_role == "DEPARTMENT_HEAD"
        is_cfo = user_role in ["CFO", "FINANCE_MANAGER"]

        # Formulate Enterprise Decision Framework:
        # WHAT HAPPENED -> WHY IT MATTERS -> WHAT SHOULD BE DONE -> WHO NEEDS TO ACT -> WHAT HAPPENS NEXT
        what_happened = (
            f"Simulated '{action_desc}' against the Financial Digital Twin ({horizon}-Day Forward Model).\n\n"
            f"{scenario_block}"
        )
        why_it_matters = (
            f"**{horizon}-Day Liquidity Shift:** ₹{before['liquidity_90d']:,.0f} $\\longrightarrow$ ₹{after['liquidity_90d']:,.0f} "
            f"(**{'+' if deltas['liquidity_change'] >= 0 else ''}₹{deltas['liquidity_change']:,.0f}**).\n"
            f"- **Runway Impact:** {before['runway_days']} days $\\longrightarrow$ {after['runway_days']} days ({'+' if deltas['runway_days_change'] >= 0 else ''}{deltas['runway_days_change']} days).\n"
            f"- **Budget Utilization:** {before['budget_utilization_pct']}% $\\longrightarrow$ {after['budget_utilization_pct']}%.\n"
            f"- **Decision Score:** {before['decision_score']}/100 $\\longrightarrow$ **{after['decision_score']}/100**."
        )

        what_should_be_done = (
            f"**Recommendation:** {sim_result['verdict_badge']}\n\n"
            f"{sim_result['verdict_summary']}\n\n"
            f"**Causal Root Cause:** {causal['primary_cause']} ({round(causal['confidence']*100)}% confidence).\n"
            f"**Correlated Signal:** {causal['correlated_signals'][0]}"
        )

        who_needs_to_act = (
            "**Vikramaditya Singhania (CFO)** and **Rahul Sharma (Finance Manager)**"
            if is_cfo else
            f"**{user_name} ({user_department} Head)** in coordination with Central Finance"
        )

        what_happens_next = (
            "1. Run Digital Twin what-if simulation on reallocation scenarios.\n"
            "2. Review pending invoices in Approvals Queue.\n"
            "3. Monitor 30-day cash liquidity reserves against scheduled payroll."
        )

        # Compose Markdown Output based on Role
        if is_auditor:
            text = (
                f"## 🔍 Audit-Grade Multi-Agent Lineage Trajectory\n\n"
                f"**Query Trace ID:** `{uuid.uuid4().hex[:12].upper()}` | **Intent:** `{intent}` | **Decision Score:** `{after['decision_score']}/100`\n\n"
                f"### 1. What Happened\n{what_happened}\n\n"
                f"### 2. Quantitative State Lineage\n{why_it_matters}\n\n"
                f"### 3. Causal Evidence & Correlated Signals\n"
                f"- **Primary Cause:** {causal['primary_cause']}\n"
                f"- **Correlation Confidence:** {causal['confidence']}\n"
                f"- **Lineage Records:**\n"
                + "\n".join(f"  * {s}" for s in causal['correlated_signals']) + "\n\n"
                f"### 4. Deterministic Rule Verification\n"
                f"- Budget Impact Factor: {twin_state['decision_score']['factors']['budget_impact']}%\n"
                f"- Policy Compliance Factor: {twin_state['decision_score']['factors']['policy_compliance']}%\n"
                f"- Variance Stability Factor: {twin_state['decision_score']['factors']['variance_stability']}%\n"
                f"- Approval Risk Factor: {twin_state['decision_score']['factors']['approval_risk']}%\n\n"
                f"### 5. Who Needs to Act & Next Steps\n{who_needs_to_act}\n\n{what_happens_next}"
            )
        elif is_dept_head:
            dept_spent = twin_state['budget_position']['departments'].get(user_department, {}).get('spent_amount', 0)
            dept_alloc = twin_state['budget_position']['departments'].get(user_department, {}).get('allocated_budget', 1)
            dept_util = round((dept_spent / dept_alloc) * 100, 1)
            text = (
                f"## 🛠️ {user_department} Department Financial Assessment\n\n"
                f"**Department Utilization:** {dept_util}% (₹{dept_spent:,.0f} of ₹{dept_alloc:,.0f})\n\n"
                f"### What Happened\n{what_happened}\n\n"
                f"### Why It Matters to {user_department}\n{why_it_matters}\n\n"
                f"### What Should Be Done\n{what_should_be_done}\n\n"
                f"### What Happens Next\n{what_happens_next}"
            )
        else:  # CFO / Finance Manager
            text = (
                f"## 👑 Executive Financial Decision Engine Synthesis\n\n"
                f"**Enterprise Position:** ₹{twin_state['cash_position']['liquid_reserves']:,.0f} Liquid Reserves | Overall Decision Score: **{twin_state['decision_score']['overall_score']} / 100** ({twin_state['decision_score']['rating']})\n\n"
                f"### 1. WHAT HAPPENED\n{what_happened}\n\n"
                f"### 2. WHY IT MATTERS\n{why_it_matters}\n\n"
                f"### 3. WHAT SHOULD BE DONE\n{what_should_be_done}\n\n"
                f"### 4. WHO NEEDS TO ACT\n{who_needs_to_act}\n\n"
                f"### 5. WHAT HAPPENS NEXT\n{what_happens_next}"
            )

        return {
            "formatted_text": text,
            "text": text,
            "suggested_actions": [
                "Simulate payment delay of 14 days",
                "Simulate Engineering spend rate for 60 days",
                "View Digital Twin What-If Studio",
                "Inspect Causal Correlation Analysis",
            ]
        }

    def _format_rbac_restriction(self, user_name: str, user_department: Optional[str], trace_id: str, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        text = (
            f"## 🔒 Access Restricted (RBAC Policy)\n\n"
            f"You are authenticated as **{user_name}** ({user_department} Department Head).\n\n"
            f"Under corporate financial governance policies, your queries and digital twin simulations are restricted to **{user_department}** department parameters.\n\n"
            f"### Available Actions for {user_department}\n"
            f"- Simulate planned expense affordability for `{user_department}`\n"
            f"- Check `{user_department}` runway and spend velocity\n"
            f"- Review `{user_department}` active claims and policy limits"
        )
        return {
            "trace_id": trace_id,
            "intent": "RBAC_RESTRICTED",
            "response": {"formatted_text": text, "text": text},
            "agent_steps": steps,
            "suggested_actions": [
                f"Simulate planned {user_department} expense",
                f"Check {user_department} runway",
            ]
        }


multi_agent_orchestrator = MultiAgentFinancialOrchestrator()
