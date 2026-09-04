import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from src.app.services.budget_service import budget_service
from src.app.services.invoice_service import invoice_service

logger = logging.getLogger("CashFlowService")


class CashFlowForecastingService:
    """
    Predictive Cash Flow & Liquidity Forecasting Engine.
    Generates 7-Day, 30-Day, 90-Day, and Fiscal Year liquidity projections.
    """

    def __init__(self):
        self.base_liquidity = 8435000.0  # Current available company liquidity in INR
        self.monthly_payroll = 850000.0  # Monthly scheduled employee payroll
        self.weekly_inflow_avg = 480000.0  # Expected gateway settlements & client receivables
        self.monthly_tax_reserve = 120000.0  # Monthly GST/TDS tax remittance reserve

    def generate_cash_forecast(
        self,
        user_role: Optional[str] = None,
        user_department: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculates multi-horizon cash curves, burn velocities, and liquidity risk.
        """
        all_invoices = invoice_service.get_all_invoices(user_role, user_department)
        pending_invoices_amt = sum(float(inv.get("total_amount", 0.0)) for inv in all_invoices if inv.get("status") == "pending_approval")

        # 1. 7-Day Horizon
        inflow_7d = self.weekly_inflow_avg * 1.0
        outflow_7d = pending_invoices_amt * 0.4 + 95000.0  # Operations & vendor clearing
        net_7d = inflow_7d - outflow_7d
        liquidity_7d = self.base_liquidity + net_7d

        # 2. 30-Day Horizon
        inflow_30d = self.weekly_inflow_avg * 4.3
        outflow_30d = self.monthly_payroll + pending_invoices_amt + self.monthly_tax_reserve + 240000.0
        net_30d = inflow_30d - outflow_30d
        liquidity_30d = self.base_liquidity + net_30d

        # 3. 90-Day Horizon
        inflow_90d = self.weekly_inflow_avg * 13.0
        outflow_90d = (self.monthly_payroll * 3.0) + (self.monthly_tax_reserve * 3.0) + (pending_invoices_amt * 2.5) + 680000.0
        net_90d = inflow_90d - outflow_90d
        liquidity_90d = self.base_liquidity + net_90d

        # 4. Fiscal Year Runway (Remaining 7 months)
        remaining_months = 7.0
        inflow_fy = self.weekly_inflow_avg * 4.3 * remaining_months
        outflow_fy = (self.monthly_payroll * remaining_months) + (self.monthly_tax_reserve * remaining_months) + (450000.0 * remaining_months)
        net_fy = inflow_fy - outflow_fy
        liquidity_fy = self.base_liquidity + net_fy

        # Risk Classification
        if liquidity_90d < 4000000.0:
            risk_level = "HIGH"
            risk_badge = "🔴 HIGH LIQUIDITY RISK"
        elif liquidity_90d < 6500000.0:
            risk_level = "MEDIUM"
            risk_badge = "🟡 MEDIUM LIQUIDITY PRESSURE"
        else:
            risk_level = "LOW"
            risk_badge = "🟢 HEALTHY LIQUIDITY"

        # Daily trajectory generation for charts (30 points)
        daily_curve = []
        running_cash = self.base_liquidity
        start_date = datetime.now()
        for day in range(1, 31):
            dt = start_date + timedelta(days=day)
            # Inflow on business days (Mon-Fri)
            daily_in = (self.weekly_inflow_avg / 5.0) if dt.weekday() < 5 else 0.0
            # Payroll spike on 1st of month, regular operational burn elsewhere
            daily_out = 45000.0
            if day == 10:  # Scheduled vendor payout batch
                daily_out += 350000.0
            elif day == 28:  # Scheduled monthly payroll
                daily_out += self.monthly_payroll

            running_cash = running_cash + daily_in - daily_out
            daily_curve.append({
                "day": day,
                "date": dt.strftime("%Y-%m-%d"),
                "projected_cash": round(running_cash, 2),
                "inflow": round(daily_in, 2),
                "outflow": round(daily_out, 2),
            })

        explanation = (
            f"Current company liquidity of ₹{self.base_liquidity:,.2f} is projected to adjust to ₹{liquidity_30d:,.2f} in 30 days "
            f"and ₹{liquidity_90d:,.2f} in 90 days. The primary outflow driver is the scheduled monthly payroll (₹{self.monthly_payroll:,.2f}/mo) "
            f"and ₹{pending_invoices_amt:,.2f} in pending vendor disbursements."
        )

        return {
            "current_liquidity": self.base_liquidity,
            "horizons": {
                "seven_day": {
                    "projected_liquidity": round(liquidity_7d, 2),
                    "net_change": round(net_7d, 2),
                    "expected_inflow": round(inflow_7d, 2),
                    "expected_outflow": round(outflow_7d, 2),
                },
                "thirty_day": {
                    "projected_liquidity": round(liquidity_30d, 2),
                    "net_change": round(net_30d, 2),
                    "expected_inflow": round(inflow_30d, 2),
                    "expected_outflow": round(outflow_30d, 2),
                },
                "ninety_day": {
                    "projected_liquidity": round(liquidity_90d, 2),
                    "net_change": round(net_90d, 2),
                    "expected_inflow": round(inflow_90d, 2),
                    "expected_outflow": round(outflow_90d, 2),
                },
                "fiscal_year": {
                    "projected_liquidity": round(liquidity_fy, 2),
                    "net_change": round(net_fy, 2),
                }
            },
            "risk_level": risk_level,
            "risk_badge": risk_badge,
            "ai_explanation": explanation,
            "daily_curve": daily_curve,
            # Structured driver records for the "Key Outflow & Liquidity Drivers"
            # dashboard card (frontend reads forecast.recurring_drivers).
            "recurring_drivers": [
                {
                    "name": "Monthly Corporate Payroll",
                    "frequency": "Monthly",
                    "department": "All Departments",
                    "amount": round(self.monthly_payroll, 2),
                },
                {
                    "name": "Pending Vendor Disbursements",
                    "frequency": "On approval",
                    "department": "Finance",
                    "amount": round(pending_invoices_amt, 2),
                },
                {
                    "name": "Statutory Tax Remittance Reserve",
                    "frequency": "Monthly",
                    "department": "Finance",
                    "amount": round(self.monthly_tax_reserve, 2),
                },
                {
                    "name": "Operational Overhead & Vendor Clearing",
                    "frequency": "Monthly",
                    "department": "Operations",
                    "amount": 240000.0,
                },
            ],
            "key_drivers": [
                f"Monthly Corporate Payroll: ₹{self.monthly_payroll:,.2f}/month",
                f"Pending Vendor Disbursements: ₹{pending_invoices_amt:,.2f}",
                f"Weekly Gateway Receivables: ~₹{self.weekly_inflow_avg:,.2f}/week",
                f"Statutory Tax Remittance Reserve: ₹{self.monthly_tax_reserve:,.2f}/month",
            ]
        }


cash_flow_service = CashFlowForecastingService()
