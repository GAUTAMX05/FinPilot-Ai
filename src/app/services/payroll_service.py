import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.app.services.employee_finance_service import employee_finance_service
from src.app.services.audit_service import audit_service

logger = logging.getLogger("PayrollService")


class PayrollAndTaxReconciliationService:
    """
    Payroll Analyzer, Salary Bill Cross-Checker, Form 16 / TDS Reconciler,
    and Headcount Cost Forecasting Engine.
    """

    def __init__(self):
        self._payroll_records = self._init_payroll_records()
        self._tax_records = self._init_tax_records()

    def _init_payroll_records(self) -> List[Dict[str, Any]]:
        return [
            {
                "payroll_batch_id": "PAY-2026-08",
                "employee_id": "EMP-101",
                "name": "Rahul Sharma",
                "department": "Engineering",
                "basic_salary": 75000.0,
                "allowances_claimed": 12000.0,
                "expected_gross": 87000.0,
                "payroll_gross": 95000.0,  # Intentional ₹8,000 mismatch for anomaly detection
                "deductions_pf": 9000.0,
                "tax_tds": 12500.0,
                "net_salary_paid": 73500.0,
                "status": "MISMATCH_DETECTED",
                "mismatch_amount": 8000.0,
                "mismatch_explanation": "Payroll gross (₹95,000) exceeds expected salary + approved allowances (₹87,000) by ₹8,000.",
            },
            {
                "payroll_batch_id": "PAY-2026-08",
                "employee_id": "EMP-102",
                "name": "Priya Verma",
                "department": "Engineering",
                "basic_salary": 145000.0,
                "allowances_claimed": 18000.0,
                "expected_gross": 163000.0,
                "payroll_gross": 163000.0,
                "deductions_pf": 17400.0,
                "tax_tds": 28500.0,
                "net_salary_paid": 117100.0,
                "status": "COMPLIANT",
                "mismatch_amount": 0.0,
                "mismatch_explanation": "All calculations validated against approved master records.",
            },
            {
                "payroll_batch_id": "PAY-2026-08",
                "employee_id": "EMP-103",
                "name": "Aman Mehra",
                "department": "Marketing",
                "basic_salary": 82000.0,
                "allowances_claimed": 14800.0,
                "expected_gross": 96800.0,
                "payroll_gross": 96800.0,
                "deductions_pf": 9840.0,
                "tax_tds": 14500.0,
                "net_salary_paid": 72460.0,
                "status": "COMPLIANT",
                "mismatch_amount": 0.0,
                "mismatch_explanation": "100% matched with master data.",
            },
            {
                "payroll_batch_id": "PAY-2026-08",
                "employee_id": "EMP-104",
                "name": "Kavita Iyer",
                "department": "Finance",
                "basic_salary": 90000.0,
                "allowances_claimed": 4500.0,
                "expected_gross": 94500.0,
                "payroll_gross": 94500.0,
                "deductions_pf": 10800.0,
                "tax_tds": 16200.0,
                "net_salary_paid": 67500.0,
                "status": "COMPLIANT",
                "mismatch_amount": 0.0,
                "mismatch_explanation": "Validated against master contract.",
            }
        ]

    def _init_tax_records(self) -> List[Dict[str, Any]]:
        return [
            {
                "employee_id": "EMP-101",
                "name": "Rahul Sharma",
                "pan": "ABCPS8841K",
                "tan_employer": "BLRRA19284K",
                "assessment_year": "AY 2027-28",
                "financial_year": "FY 2026-27",
                "form16_gross_salary": 1044000.0,
                "payroll_annualized_salary": 1140000.0,
                "salary_difference": 96000.0,
                "tds_deducted_employer": 150000.0,
                "tds_deposited_26as": 150000.0,
                "tds_difference": 0.0,
                "status": "SALARY_REPORTING_MISMATCH",
                "explanation": "Form 16 reported gross (₹10.44L) differs from annualized payroll gross (₹11.40L) by ₹96,000. Verification required before quarterly return filing.",
                "recommended_action": "Review salary components contributing to the ₹96,000 difference.",
            },
            {
                "employee_id": "EMP-102",
                "name": "Priya Verma",
                "pan": "BCDPV9912L",
                "tan_employer": "BLRRA19284K",
                "assessment_year": "AY 2027-28",
                "financial_year": "FY 2026-27",
                "form16_gross_salary": 1956000.0,
                "payroll_annualized_salary": 1956000.0,
                "salary_difference": 0.0,
                "tds_deducted_employer": 342000.0,
                "tds_deposited_26as": 342000.0,
                "tds_difference": 0.0,
                "status": "FULLY_RECONCILED",
                "explanation": "100% match between Form 16, payroll register, and Form 26AS tax credits.",
                "recommended_action": "No action required.",
            },
            {
                "employee_id": "EMP-103",
                "name": "Aman Mehra",
                "pan": "CDEAM7731M",
                "tan_employer": "BLRRA19284K",
                "assessment_year": "AY 2027-28",
                "financial_year": "FY 2026-27",
                "form16_gross_salary": 1161600.0,
                "payroll_annualized_salary": 1161600.0,
                "salary_difference": 0.0,
                "tds_deducted_employer": 174000.0,
                "tds_deposited_26as": 174000.0,
                "tds_difference": 0.0,
                "status": "FULLY_RECONCILED",
                "explanation": "Form 16 matches annualized payroll calculations.",
                "recommended_action": "No action required.",
            },
            {
                "employee_id": "EMP-104",
                "name": "Kavita Iyer",
                "pan": "DEFKI3321N",
                "tan_employer": "BLRRA19284K",
                "assessment_year": "AY 2027-28",
                "financial_year": "FY 2026-27",
                "form16_gross_salary": 1134000.0,
                "payroll_annualized_salary": 1134000.0,
                "salary_difference": 0.0,
                "tds_deducted_employer": 194400.0,
                "tds_deposited_26as": 194400.0,
                "tds_difference": 0.0,
                "status": "FULLY_RECONCILED",
                "explanation": "Form 16 Part A and Part B fully reconciled.",
                "recommended_action": "No action required.",
            },
            {
                "employee_id": "EMP-1042",
                "name": "Siddharth Verma",
                "pan": "FGHSV4492P",
                "tan_employer": "BLRRA19284K",
                "assessment_year": "AY 2027-28",
                "financial_year": "FY 2026-27",
                "form16_gross_salary": 875000.0,
                "payroll_annualized_salary": 840000.0,
                "salary_difference": 35000.0,
                "tds_deducted_employer": 72000.0,
                "tds_deposited_26as": 72000.0,
                "tds_difference": 0.0,
                "status": "SALARY_REPORTING_MISMATCH",
                "explanation": "Payroll salary (₹8,40,000) differs from Form 16 reported gross (₹8,75,000) by ₹35,000.",
                "recommended_action": "Review salary components and reconcile difference with payroll ledger.",
            }
        ]

    # =========================================================================
    # PAYROLL ANALYSIS & CROSS-CHECK
    # =========================================================================

    def get_payroll_summary(
        self,
        user_role: Optional[str] = None,
        user_department: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Returns corporate payroll register and cross-check telemetry."""
        records = self._payroll_records
        if user_role == "DEPARTMENT_HEAD" and user_department:
            records = [r for r in records if r["department"].lower() == user_department.lower()]

        total_gross = sum(r["payroll_gross"] for r in records)
        total_net = sum(r["net_salary_paid"] for r in records)
        total_tds = sum(r["tax_tds"] for r in records)
        total_pf = sum(r["deductions_pf"] for r in records)
        mismatch_count = sum(1 for r in records if r["status"] == "MISMATCH_DETECTED")

        return {
            "payroll_month": "August 2026 (FY 2026–27)",
            "employee_count": len(records),
            "total_gross_disbursed": total_gross,
            "total_net_payout": total_net,
            "total_tds_withheld": total_tds,
            "total_pf_deductions": total_pf,
            "mismatch_count": mismatch_count,
            "compliance_status": "COMPLIANT" if mismatch_count == 0 else "REVIEW REQUIRED",
            "records": records,
        }

    # =========================================================================
    # FORM 16 / TDS TAX RECONCILIATION
    # =========================================================================

    def get_tax_reconciliation(
        self,
        user_role: Optional[str] = None,
        user_department: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Reconciles Form 16 certificates against employer-deposited TDS and annualized payroll."""
        records = self._tax_records
        reconciled_count = sum(1 for r in records if r["status"] == "FULLY_RECONCILED")
        mismatch_count = sum(1 for r in records if r["status"] == "SALARY_REPORTING_MISMATCH")

        return {
            "financial_year": "FY 2026-2027",
            "assessment_year": "AY 2027-2028",
            "total_records_audited": len(records),
            "fully_reconciled_count": reconciled_count,
            "salary_mismatch_count": mismatch_count,
            "tds_mismatch_count": sum(1 for r in records if r["tds_difference"] > 0),
            "form16_uploaded_count": len(records),
            "form16_pending_count": 1,
            "records": records,
        }

    def resolve_tax_record(
        self,
        employee_id: str,
        resolution_note: str,
        user_id: str,
        user_name: str,
        user_role: str,
    ) -> Dict[str, Any]:
        """Marks a tax reporting mismatch as reviewed and resolved."""
        for rec in self._tax_records:
            if rec["employee_id"].lower() == employee_id.lower():
                rec["status"] = "RESOLVED"
                rec["resolved_by"] = user_name
                rec["resolved_at"] = datetime.now().isoformat()
                rec["resolution_note"] = resolution_note or "Manually verified against adjusted salary annexure."

                audit_service.log_action(
                    user_id=user_id,
                    user_name=user_name,
                    role=user_role,
                    action="RESOLVE_FORM16_TAX_MISMATCH",
                    entity="TAX_RECORD",
                    entity_id=employee_id,
                    new_value="RESOLVED",
                    details=f"Resolved Form 16 / Payroll mismatch for {rec['name']}. Note: {rec['resolution_note']}",
                    risk_level="MEDIUM",
                )

                return {
                    "success": True,
                    "message": f"Tax record for {rec['name']} marked as Resolved.",
                    "tax_record": rec,
                }

        raise ValueError(f"Tax record for employee '{employee_id}' not found.")

    def notify_finance_for_tax(
        self,
        employee_id: str,
        user_name: str,
        user_role: str,
    ) -> Dict[str, Any]:
        """Dispatches notification to the finance department for tax reconciliation."""
        for rec in self._tax_records:
            if rec["employee_id"].lower() == employee_id.lower():
                rec["finance_notified"] = True
                rec["finance_notified_at"] = datetime.now().isoformat()

                audit_service.log_action(
                    user_id="SYSTEM",
                    user_name=user_name,
                    role=user_role,
                    action="NOTIFY_FINANCE_TAX",
                    entity="TAX_RECORD",
                    entity_id=employee_id,
                    details=f"Alerted Finance Operations regarding Form 16 mismatch for {rec['name']} (Diff: ₹{rec['salary_difference']:,.2f}).",
                    risk_level="LOW",
                )

                return {
                    "success": True,
                    "message": f"Finance Operations alerted for {rec['name']} Form 16 reconciliation.",
                    "tax_record": rec,
                }

        raise ValueError(f"Tax record for employee '{employee_id}' not found.")

    # =========================================================================
    # HEADCOUNT COST BREAKDOWN & GROWTH FORECASTING
    # =========================================================================

    def get_headcount_cost_analytics(self) -> Dict[str, Any]:
        """Calculates total employee headcount costs and models 6, 12, and 24-month cost growth."""
        base_annual_cost = 9510000.0  # ₹95.10 Lakhs annual employee cost
        current_headcount = 14

        return {
            "current_headcount": current_headcount,
            "total_annual_employee_cost": base_annual_cost,
            "cost_breakdown": {
                "direct_salaries": base_annual_cost * 0.72,
                "base_salaries": base_annual_cost * 0.72,
                "employee_allowances": base_annual_cost * 0.14,
                "allowances_and_reimbursements": base_annual_cost * 0.14,
                "wellness_and_benefits": base_annual_cost * 0.05,
                "employer_statutory_pf": base_annual_cost * 0.09,
                "statutory_benefits_pf_gratuity": base_annual_cost * 0.09,
                "learning_wellness_perks": base_annual_cost * 0.05,
            },
            "department_cost_distribution": {
                "Engineering": {"annual_cost": 2860000.0},
                "Marketing": {"annual_cost": 1545000.0},
                "Finance": {"annual_cost": 1800000.0},
                "Sales": {"annual_cost": 1950000.0},
                "Operations": {"annual_cost": 1355000.0},
            },
            "headcount_growth_forecast": {
                "six_months": {
                    "projected_headcount": 16,
                    "projected_annual_cost": base_annual_cost * 1.08,
                    "growth_pct": 8.0,
                    "growth_percentage": 8.0,
                },
                "twelve_months": {
                    "projected_headcount": 18,
                    "projected_annual_cost": base_annual_cost * 1.16,
                    "growth_pct": 16.0,
                    "growth_percentage": 16.0,
                },
                "twenty_four_months": {
                    "projected_headcount": 22,
                    "projected_annual_cost": base_annual_cost * 1.34,
                    "growth_pct": 34.0,
                    "growth_percentage": 34.0,
                }
            },
            "ai_executive_takeaway": "Headcount growth trajectory is sustainable within FY 2026-2027 revenue run-rate projections. Engineering accounts for largest portion of total talent spend.",
        }


payroll_service = PayrollAndTaxReconciliationService()
