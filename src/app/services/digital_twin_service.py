import copy
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.app.services.budget_service import budget_service
from src.app.services.invoice_service import invoice_service
from src.app.services.employee_finance_service import employee_finance_service
from src.app.services.payroll_service import payroll_service
from src.app.services.cash_flow_service import cash_flow_service

logger = logging.getLogger("FinancialDigitalTwin")

# Employer-loaded cost factor applied to monthly basic to reach gross payroll
# (PF 12% + allowances/overheads), consistent with simulate_forward grossing.
PAYROLL_LOAD_FACTOR = 1.4

_WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "fifteen": 15, "twenty": 20, "thirty": 30, "fifty": 50,
}


def _parse_horizon_days(text: str, default: int = 90) -> int:
    """Extracts a projection horizon (days) from natural language. Clamped 14–180."""
    t = text.lower()
    m = re.search(r"(\d+)\s*(?:more\s+)?days?\b", t)
    if m:
        try:
            return max(14, min(180, int(m.group(1))))
        except ValueError:
            pass
    m = re.search(r"(\d+)\s*weeks?\b", t)
    if m:
        try:
            return max(14, min(180, int(m.group(1)) * 7))
        except ValueError:
            pass
    m = re.search(r"(\d+)\s*months?\b", t)
    if m:
        try:
            return max(14, min(180, int(m.group(1)) * 30))
        except ValueError:
            pass
    return default


def _parse_headcount(text: str, default: int = 3) -> int:
    """Extracts a headcount figure using anchored regex (never bare substring match)."""
    t = text.lower()
    for pattern in (
        r"(\d+)\s+(?:senior\s+|junior\s+)?engineers?\b",
        r"\bhir(?:e|es|ing)\s+(\d+)\b",
        r"headcount[^0-9\n]{0,40}?(\d+)\b",
        r"team\s+of\s+(\d+)\b",
        r"add\s+(\d+)\s+\w+",
    ):
        m = re.search(pattern, t)
        if m:
            try:
                return max(1, min(500, int(m.group(1))))
            except ValueError:
                continue
    for word, val in _WORD_NUMBERS.items():
        if re.search(rf"\b{word}\b\s+(?:senior\s+|junior\s+)?engineers?\b", t):
            return val
    return default


def _parse_monthly_salary(text: str, default: float = 85000.0) -> float:
    """Extracts a monthly-basic salary figure (supports ₹/Rs./lakh/k suffixes)."""
    t = text.lower()
    for pattern in (
        r"₹\s*([\d,]+(?:\.\d+)?)\s*(k|lakh|lakhs|lac|m)?\b",
        r"\brs\.?\s*([\d,]+(?:\.\d+)?)\s*(k|lakh|lakhs|lac|m)?\b",
        r"([\d,]+(?:\.\d+)?)\s*(k|lakh|lakhs|lac|m)?\s*(?:per\s+month\s+)?monthly\s+basic\b",
        r"basic[^0-9\n]{0,20}?([\d,]+(?:\.\d+)?)\b",
    ):
        m = re.search(pattern, t)
        if m:
            try:
                val = float(m.group(1).replace(",", ""))
                unit = (m.group(2) or "").strip() if len(m.groups()) > 1 else ""
                if unit == "k":
                    val *= 1000.0
                elif unit in ("lakh", "lakhs", "lac"):
                    val *= 100000.0
                elif unit == "m":
                    val *= 1000000.0
                if 5000.0 <= val <= 5000000.0:
                    return val
            except ValueError:
                continue
    return default


def _parse_department(text: str, default: str = "Operations") -> str:
    t = text.lower()
    for dept in ("engineering", "marketing", "sales", "operations", "hr"):
        if re.search(rf"\b{dept}\b", t):
            return dept.capitalize() if dept != "hr" else "HR"
    if "eng" in t:
        return "Engineering"
    if "market" in t:
        return "Marketing"
    return default


def _parse_delay_days(text: str, default: int = 14) -> int:
    t = text.lower()
    m = re.search(r"(\d+)\s*weeks?\b", t)
    if m:
        try:
            return max(1, min(90, int(m.group(1)) * 7))
        except ValueError:
            pass
    m = re.search(r"(\d+)\s*days?\b", t)
    if m:
        try:
            return max(1, min(90, int(m.group(1))))
        except ValueError:
            pass
    return default


class FinancialDigitalTwin:
    """
    Live simulate-able in-memory financial digital twin of the enterprise.
    Maintains synchronized state of cash reserves, department allocations,
    burn rates, headcount commitments, vendor obligations, and tax liabilities.
    Enables forward day-by-day simulations and counterfactual what-if branch testing.
    """

    def __init__(self):
        self._cached_snapshot: Optional[Dict[str, Any]] = None
        self._last_snapshot_time: Optional[datetime] = None

    def get_live_state(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Captures a coherent snapshot of the entire enterprise financial state."""
        now = datetime.utcnow()
        if not force_refresh and self._cached_snapshot and self._last_snapshot_time:
            if (now - self._last_snapshot_time).total_seconds() < 10:
                return copy.deepcopy(self._cached_snapshot)

        # 1. Cash & Liquidity
        cf_data = cash_flow_service.generate_cash_forecast()
        current_liquidity = cf_data.get("current_liquidity", 8435000.0)

        # 2. Department Budgets
        budgets_raw = budget_service.get_all_departments()
        departments: Dict[str, Dict[str, Any]] = {}
        total_allocated = 0.0
        total_spent = 0.0
        total_monthly_burn = 0.0

        for dept_name, info in budgets_raw.items():
            alloc = float(info.get("allocated_budget", 0.0))
            spent = float(info.get("spent_amount", 0.0))
            pending = float(info.get("pending_approvals", 0.0))
            # Current fiscal elapsed ~ 5 months
            monthly_burn = round(spent / 5.0, 2) if spent > 0 else round(alloc / 12.0, 2)

            departments[dept_name] = {
                "name": dept_name,
                "allocated_budget": alloc,
                "spent_amount": spent,
                "pending_approvals": pending,
                "remaining_budget": max(0.0, alloc - spent),
                "monthly_burn_rate": monthly_burn,
                "projected_year_end": round(spent + (monthly_burn * 7.0), 2),
                "manager": info.get("manager", "Lead"),
                "categories": info.get("categories", {}),
            }
            total_allocated += alloc
            total_spent += spent
            total_monthly_burn += monthly_burn

        # 3. Payroll & Headcount
        employees_raw = employee_finance_service.get_all_employees()
        total_monthly_basic = sum(emp.get("monthly_basic", 0.0) for emp in employees_raw)
        total_monthly_gross = sum(emp.get("computed_compensation", {}).get("gross_salary", emp.get("monthly_basic", 0.0) * 1.4) for emp in employees_raw)
        total_headcount = len(employees_raw)

        # 4. Invoices & Commitments (status match is case-insensitive: seeded
        # statuses are "Pending Review"/"Approved"/"Paid", legacy code used
        # "pending_approval"/"approved").
        invoices_raw = invoice_service.get_all_invoices()
        pending_invoices = [inv for inv in invoices_raw if str(inv.get("status", "")).lower() in ("pending review", "pending_approval", "pending")]
        approved_invoices = [inv for inv in invoices_raw if str(inv.get("status", "")).lower() in ("approved", "paid")]
        total_pending_amount = sum(float(inv.get("total_amount", 0.0)) for inv in pending_invoices)

        # 5. Composite Decision Score Calculation
        overall_utilization = (total_spent / total_allocated * 100) if total_allocated > 0 else 0
        budget_impact_factor = max(0.0, min(100.0, 100.0 - (overall_utilization - 35.0) * 2.0))
        policy_compliance_factor = 91.0
        variance_stability_factor = 68.0
        approval_risk_factor = 84.0

        decision_score = round(
            budget_impact_factor * 0.30 +
            policy_compliance_factor * 0.25 +
            variance_stability_factor * 0.25 +
            approval_risk_factor * 0.20,
            1
        )

        snapshot = {
            "timestamp": now.isoformat(),
            "cash_position": {
                "liquid_reserves": current_liquidity,
                "receivables_7d": 480000.0,
                "inflows_daily_avg": 68571.4,
                "recurring_outflows_monthly": 1150000.0,
                "safe_liquidity_threshold": 3000000.0,
            },
            "budget_position": {
                "total_allocated": total_allocated,
                "total_spent": total_spent,
                "total_remaining": total_allocated - total_spent,
                "total_monthly_burn": total_monthly_burn,
                "utilization_pct": round(overall_utilization, 2),
                "departments": departments,
            },
            "payroll_position": {
                "headcount": total_headcount,
                "monthly_basic_total": total_monthly_basic,
                "monthly_gross_total": total_monthly_gross,
                "statutory_pf_monthly": total_monthly_basic * 0.12,
                "tds_deductions_monthly": total_monthly_gross * 0.10,
            },
            "commitments": {
                "pending_invoices_count": len(pending_invoices),
                "pending_invoices_amount": total_pending_amount,
                "approved_invoices_count": len(approved_invoices),
            },
            "decision_score": {
                "overall_score": decision_score,
                "rating": "HEALTHY" if decision_score >= 80 else ("ATTENTION" if decision_score >= 65 else "CRITICAL"),
                "factors": {
                    "budget_impact": round(budget_impact_factor, 1),
                    "policy_compliance": round(policy_compliance_factor, 1),
                    "variance_stability": round(variance_stability_factor, 1),
                    "approval_risk": round(approval_risk_factor, 1),
                }
            }
        }

        self._cached_snapshot = snapshot
        self._last_snapshot_time = now
        return copy.deepcopy(snapshot)

    def simulate_forward(
        self,
        days: int = 90,
        modifiers: Optional[Dict[str, Any]] = None,
        base_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Runs the financial digital twin forward day-by-day.
        Applies modifiers such as spend rate changes, payment delays, headcount changes, or injections.
        """
        state = copy.deepcopy(base_state) if base_state else self.get_live_state()
        mods = modifiers or {}

        # Modifier extractions
        dept_burn_multipliers = mods.get("dept_burn_multipliers", {})  # e.g. {"Engineering": 1.15}
        payment_delay_days = mods.get("payment_delay_days", 0)  # e.g. 14 days
        injected_expenses = mods.get("injected_expenses", [])  # e.g. [{"department": "Engineering", "amount": 250000, "day": 5}]
        headcount_delta = mods.get("headcount_delta", 0)  # e.g. +3 engineers
        headcount_avg_salary = mods.get("headcount_avg_salary", 75000.0)

        # Baseline parameters
        cash = state["cash_position"]["liquid_reserves"]
        daily_inflow = state["cash_position"]["inflows_daily_avg"]
        depts = copy.deepcopy(state["budget_position"]["departments"])

        # Adjust headcount payroll
        monthly_payroll = state["payroll_position"]["monthly_gross_total"]
        if headcount_delta != 0:
            added_monthly_payroll = headcount_delta * (headcount_avg_salary * 1.4)
            monthly_payroll += added_monthly_payroll

        daily_payroll_outflow = monthly_payroll / 30.0

        trajectory: List[Dict[str, Any]] = []
        labels: List[str] = []
        cash_series: List[float] = []
        burn_series: List[float] = []

        start_date = datetime.utcnow()
        deficit_detected_day: Optional[int] = None
        deficit_department: Optional[str] = None

        for day in range(1, days + 1):
            curr_date = start_date + timedelta(days=day)
            date_str = curr_date.strftime("%d %b")

            # 1. Compute daily department burn
            daily_dept_burn_total = 0.0
            for d_name, d_info in depts.items():
                mult = dept_burn_multipliers.get(d_name, 1.0)
                daily_burn = (d_info["monthly_burn_rate"] * mult) / 30.0
                d_info["spent_amount"] += daily_burn
                d_info["remaining_budget"] = max(0.0, d_info["allocated_budget"] - d_info["spent_amount"])
                daily_dept_burn_total += daily_burn

                if d_info["spent_amount"] > d_info["allocated_budget"] and not deficit_detected_day:
                    deficit_detected_day = day
                    deficit_department = d_name

            # 2. Check injected discrete events
            for exp in injected_expenses:
                if exp.get("day") == day:
                    e_dept = exp.get("department", "Operations")
                    e_amt = float(exp.get("amount", 0.0))
                    if e_dept in depts:
                        depts[e_dept]["spent_amount"] += e_amt
                        depts[e_dept]["remaining_budget"] = max(0.0, depts[e_dept]["allocated_budget"] - depts[e_dept]["spent_amount"])
                    cash -= e_amt

            # 3. Cash flow balance
            # Inflows occur daily
            cash += daily_inflow

            # Outflows: OpEx + Payroll
            # Delayed payments push out non-payroll OpEx
            if payment_delay_days > 0 and day <= payment_delay_days:
                # Operational payments frozen during delay window, only essential payroll flows
                cash -= daily_payroll_outflow
            else:
                cash -= (daily_dept_burn_total + daily_payroll_outflow)

            # Record step
            if day % (1 if days <= 14 else (5 if days <= 30 else 10)) == 0 or day == days or day == 1:
                labels.append(date_str)
                cash_series.append(round(cash, 2))
                burn_series.append(round(daily_dept_burn_total * 30.0, 2))

        # Calculate final deltas
        final_liquidity = round(cash, 2)
        total_final_spent = sum(d["spent_amount"] for d in depts.values())
        total_alloc = sum(d["allocated_budget"] for d in depts.values())
        final_utilization = round((total_final_spent / total_alloc * 100), 2) if total_alloc > 0 else 0

        # Calculate projected runway in days (time until cash hits safety threshold)
        safe_threshold = state["cash_position"]["safe_liquidity_threshold"]
        daily_net_burn = (daily_dept_burn_total + daily_payroll_outflow) - daily_inflow
        runway_days = round((final_liquidity - safe_threshold) / daily_net_burn) if daily_net_burn > 0 else 999
        runway_days = max(1, min(999, int(runway_days)))

        return {
            "simulation_days": days,
            "labels": labels,
            "cash_trajectory": cash_series,
            "monthly_burn_trajectory": burn_series,
            "final_liquidity": final_liquidity,
            "final_utilization_pct": final_utilization,
            "projected_runway_days": runway_days,
            "deficit_detected_day": deficit_detected_day,
            "deficit_department": deficit_department,
            "departments_after": depts,
        }

    def simulate_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs any single proposed financial event through the Digital Twin BEFORE execution.
        Returns a structured Before vs After delta analysis.
        """
        before_state = self.get_live_state()
        action_type = action.get("type", "EXPENSE")  # EXPENSE, REALLOCATION, SALARY_REVISION, ALLOWANCE_CHANGE, PAYMENT_DELAY
        action_desc = action.get("description", "Proposed Financial Action")
        # Projection window in days (parsed from the user's scenario, default 90).
        horizon = int(action.get("horizon_days", 90) or 90)
        horizon = max(14, min(365, horizon))

        modifiers: Dict[str, Any] = {}
        if action_type == "EXPENSE":
            amt = float(action.get("amount", 0.0))
            dept = action.get("department", "Engineering")
            modifiers["injected_expenses"] = [{"department": dept, "amount": amt, "day": 1}]
        elif action_type == "PAYMENT_DELAY":
            modifiers["payment_delay_days"] = int(action.get("days", 14))
        elif action_type == "BURN_RATE_SHIFT":
            dept = action.get("department", "Engineering")
            mult = float(action.get("multiplier", 1.15))
            modifiers["dept_burn_multipliers"] = {dept: mult}
        elif action_type == "HEADCOUNT_GROWTH":
            modifiers["headcount_delta"] = int(action.get("headcount", 3))
            modifiers["headcount_avg_salary"] = float(action.get("avg_salary", 75000.0))
        elif action_type == "REALLOCATION":
            from_dept = action.get("from_department", "Operations")
            to_dept = action.get("to_department", "Engineering")
            amt = float(action.get("amount", 250000.0))
            # Adjust allocations in before_state copy
            if from_dept in before_state["budget_position"]["departments"]:
                before_state["budget_position"]["departments"][from_dept]["allocated_budget"] -= amt
            if to_dept in before_state["budget_position"]["departments"]:
                before_state["budget_position"]["departments"][to_dept]["allocated_budget"] += amt

        # Run baseline simulation (Before) and proposed simulation (After)
        baseline_sim = self.simulate_forward(days=horizon, modifiers={}, base_state=before_state)
        # Run proposed simulation (After)
        proposed_sim = self.simulate_forward(days=horizon, modifiers=modifiers, base_state=before_state)

        # Compute explicit deltas
        liquidity_before = baseline_sim["final_liquidity"]
        liquidity_after = proposed_sim["final_liquidity"]
        liquidity_delta = round(liquidity_after - liquidity_before, 2)

        runway_before = baseline_sim["projected_runway_days"]
        runway_after = proposed_sim["projected_runway_days"]
        runway_delta = runway_after - runway_before

        utilization_before = baseline_sim["final_utilization_pct"]
        utilization_after = proposed_sim["final_utilization_pct"]
        utilization_delta = round(utilization_after - utilization_before, 2)

        score_before = before_state["decision_score"]["overall_score"]
        score_penalty = 0.0
        if liquidity_delta < -200000:
            score_penalty += 3.5
        # Scale penalty with shock size so extreme scenarios (e.g. mass hiring)
        # reach REJECT_RISK instead of sharing a badge with mild scenarios.
        if liquidity_delta < -1000000:
            score_penalty += min(20.0, abs(liquidity_delta) / 1000000.0 * 2.0)
        if utilization_delta > 5.0:
            score_penalty += 4.0
        if proposed_sim["deficit_detected_day"]:
            score_penalty += 8.0

        score_after = round(max(10.0, min(100.0, score_before - score_penalty)), 1)
        score_delta = round(score_after - score_before, 1)

        # Determine recommendation verdict
        if score_after >= 75 and liquidity_after >= before_state["cash_position"]["safe_liquidity_threshold"]:
            verdict = "APPROVED_SAFE"
            verdict_badge = "🟢 SAFE TO EXECUTE"
            verdict_summary = "The proposed action is well within capital reserves and does not induce critical deficit risk."
        elif score_after >= 60:
            verdict = "REQUIRES_GOVERNANCE"
            verdict_badge = "🟡 EXECUTIVE REVIEW ADVISED"
            verdict_summary = "Action increases burn velocity and tightens liquidity runway. Recommended to pace across quarterly milestones."
        else:
            verdict = "REJECT_RISK"
            verdict_badge = "🔴 DEFICIT RISK DETECTED"
            verdict_summary = f"Action triggers projected deficit on day {proposed_sim.get('deficit_detected_day', 45)} in {proposed_sim.get('deficit_department', 'Engineering')}. Surplus reallocation required."

        return {
            "action": action,
            "action_description": action_desc,
            "horizon_days": horizon,
            "verdict": verdict,
            "verdict_badge": verdict_badge,
            "verdict_summary": verdict_summary,
            "before": {
                "liquidity_90d": liquidity_before,
                "runway_days": runway_before,
                "budget_utilization_pct": utilization_before,
                "decision_score": score_before,
                "deficit_risk": "None projected" if not baseline_sim["deficit_detected_day"] else f"Day {baseline_sim['deficit_detected_day']} ({baseline_sim['deficit_department']})",
            },
            "after": {
                "liquidity_90d": liquidity_after,
                "runway_days": runway_after,
                "budget_utilization_pct": utilization_after,
                "decision_score": score_after,
                "deficit_risk": "None projected" if not proposed_sim["deficit_detected_day"] else f"Day {proposed_sim['deficit_detected_day']} ({proposed_sim['deficit_department']})",
            },
            "deltas": {
                "liquidity_change": liquidity_delta,
                "runway_days_change": runway_delta,
                "utilization_pct_change": utilization_delta,
                "decision_score_change": score_delta,
            },
            "trajectory_chart": {
                "labels": proposed_sim["labels"],
                "baseline_cash": baseline_sim["cash_trajectory"],
                "projected_cash": proposed_sim["cash_trajectory"],
            }
        }

    def run_what_if_scenario(self, scenario_text: str, user_role: str = "CFO", user_department: Optional[str] = None) -> Dict[str, Any]:
        """
        Parses a natural-language what-if query, executes the Digital Twin branch simulation,
        and produces structured comparative insights.
        """
        s_lower = scenario_text.lower()
        action: Dict[str, Any] = {"type": "EXPENSE", "description": scenario_text}

        # 1. Check for payment delay scenario
        if "delay" in s_lower and any(w in s_lower for w in ["vendor", "payment", "bill", "invoice", "week", "days"]):
            days = _parse_delay_days(scenario_text)
            action = {
                "type": "PAYMENT_DELAY",
                "days": days,
                "horizon_days": _parse_horizon_days(scenario_text),
                "description": f"Delay vendor non-essential disbursements by {days} days",
            }

        # 2. Check for spending rate / burn rate continuation
        elif any(w in s_lower for w in ["stay", "rate", "pace", "same", "continue"]) and any(w in s_lower for w in ["engineering", "marketing", "burn"]):
            dept = _parse_department(scenario_text, default="Operations")
            if dept == "Operations" and "burn" in s_lower and "engineering" in s_lower:
                dept = "Engineering"
            horizon = _parse_horizon_days(scenario_text)
            action = {
                "type": "BURN_RATE_SHIFT",
                "department": dept,
                "multiplier": 1.12,
                "horizon_days": horizon,
                "description": f"{dept} spending rate continues at +12% above benchmark pace for {horizon} days",
            }

        # 3. Check for headcount hiring
        elif any(w in s_lower for w in ["hire", "headcount", "recruit", "engineers", "employee", "team"]):
            count = _parse_headcount(scenario_text)
            salary = _parse_monthly_salary(scenario_text)
            horizon = _parse_horizon_days(scenario_text)
            action = {
                "type": "HEADCOUNT_GROWTH",
                "headcount": count,
                "avg_salary": salary,
                "horizon_days": horizon,
                "description": f"Hire {count} senior engineers at ₹{salary:,.0f}/mo basic",
            }

        # 4. Check for budget reallocation
        elif "reallocat" in s_lower or "transfer" in s_lower:
            action = {
                "type": "REALLOCATION",
                "from_department": "Operations",
                "to_department": "Engineering",
                "amount": 250000.0,
                "description": "Reallocate ₹250,000 budget from Operations surplus to Engineering",
            }

        # 5. Default: Expense injection
        else:
            amt = 500000.0
            match = re.search(r"(\d+(?:,\d+)*(?:\.\d+)?)\s*(k|lakh|lakhs|m)?", s_lower)
            if match:
                val = float(match.group(1).replace(",", ""))
                unit = match.group(2)
                if unit == "k": amt = val * 1000.0
                elif unit in ["lakh", "lakhs"]: amt = val * 100000.0
                elif unit == "m": amt = val * 1000000.0
                elif val < 1000: amt = val * 100000.0
                else: amt = val

            dept = _parse_department(scenario_text)
            action = {
                "type": "EXPENSE",
                "amount": amt,
                "department": dept,
                "horizon_days": _parse_horizon_days(scenario_text),
                "description": f"Disburse planned expense of ₹{amt:,.2f} for {dept}",
            }

        # Execute simulation
        sim_result = self.simulate_action(action)
        return sim_result


digital_twin_service = FinancialDigitalTwin()
