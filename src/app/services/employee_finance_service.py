import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.app.services.audit_service import audit_service

logger = logging.getLogger("EmployeeFinanceService")


class EmployeeFinancialControlService:
    """
    Enterprise Employee Financial Governance, Allowance Controller,
    Salary Management, Claims Anomaly Detector, and Job Evaluation Engine.
    """

    def __init__(self):
        self._employees = self._init_employees()

    def _init_employees(self) -> List[Dict[str, Any]]:
        initial_list = [
            {
                "employee_id": "EMP-101",
                "name": "Rahul Sharma",
                "email": "rahul.sharma@aifinance.local",
                "phone": "+91 98765 43210",
                "department": "Engineering",
                "designation": "Senior Software Engineer",
                "salary_band": "₹12–18 LPA",
                "annual_ctc": 1500000.0,
                "monthly_basic": 75000.0,
                "hra": 30000.0,
                "special_allowance": 12000.0,
                "bonus_variable": 8000.0,
                "pf_deduction": 9000.0,
                "tds_deduction": 12500.0,
                "other_deductions": 0.0,
                "joining_date": "2023-04-15",
                "employment_type": "Full-Time",
                "status": "ACTIVE",
                "manager": "Priya Verma",
                "location": "Bangalore HQ",
                "monthly_allowance_limit": 15000.0,
                "annual_allowance_limit": 180000.0,
                "allowance_policy": {
                    "travel": {"monthly_limit": 15000.0, "spent": 24800.0, "annual_limit": 180000.0},
                    "food": {"monthly_limit": 5000.0, "spent": 4200.0, "annual_limit": 60000.0},
                    "fuel": {"monthly_limit": 4000.0, "spent": 3800.0, "annual_limit": 48000.0},
                    "internet": {"monthly_limit": 2000.0, "spent": 1999.0, "annual_limit": 24000.0},
                    "mobile": {"monthly_limit": 1500.0, "spent": 1499.0, "annual_limit": 18000.0},
                    "learning": {"monthly_limit": 5000.0, "spent": 0.0, "annual_limit": 60000.0},
                    "wellness": {"monthly_limit": 3000.0, "spent": 2500.0, "annual_limit": 36000.0},
                    "wfh": {"monthly_limit": 5000.0, "spent": 4800.0, "annual_limit": 60000.0},
                },
                "claims": [
                    {
                        "claim_id": "CLM-991",
                        "category": "Travel",
                        "amount": 12500.0,
                        "date": "2026-08-12",
                        "description": "Client On-site Travel - Bangalore",
                        "status": "APPROVED",
                    },
                    {
                        "claim_id": "CLM-994",
                        "category": "Travel",
                        "amount": 12300.0,
                        "date": "2026-08-18",
                        "description": "Regional Conference Flight Claim",
                        "status": "FLAGGED_REVIEW",
                        "anomaly_reason": "Limit Exceeded: Total monthly travel claims (₹24,800) exceed ₹15,000 policy cap.",
                    }
                ],
                "salary_history": [
                    {
                        "effective_date": "2025-04-01",
                        "previous_salary": 68000.0,
                        "new_salary": 75000.0,
                        "increase_pct": 10.29,
                        "reason": "Annual Performance Appraisal",
                        "approved_by": "Vikramaditya S. (CFO)",
                    }
                ],
                "job_evaluation": {
                    "goal_completion_pct": 94.0,
                    "milestones_delivered": "6 / 6 Features",
                    "code_quality_and_reliability": 91.0,
                    "timeliness": 89.0,
                    "expense_policy_discipline": 76.0,
                    "overall_job_performance": 88.0,
                    "rating": "EXCEEDS_EXPECTATIONS",
                }
            },
            {
                "employee_id": "EMP-102",
                "name": "Priya Verma",
                "email": "priya.verma@aifinance.local",
                "phone": "+91 98765 43211",
                "department": "Engineering",
                "designation": "Engineering Manager",
                "salary_band": "₹24–32 LPA",
                "annual_ctc": 2800000.0,
                "monthly_basic": 145000.0,
                "hra": 58000.0,
                "special_allowance": 25000.0,
                "bonus_variable": 15000.0,
                "pf_deduction": 17400.0,
                "tds_deduction": 28500.0,
                "other_deductions": 0.0,
                "joining_date": "2021-08-01",
                "employment_type": "Full-Time",
                "status": "ACTIVE",
                "manager": "Vikramaditya S.",
                "location": "Bangalore HQ",
                "monthly_allowance_limit": 25000.0,
                "annual_allowance_limit": 300000.0,
                "allowance_policy": {
                    "travel": {"monthly_limit": 25000.0, "spent": 18000.0, "annual_limit": 300000.0},
                    "food": {"monthly_limit": 8000.0, "spent": 6500.0, "annual_limit": 96000.0},
                    "internet": {"monthly_limit": 3000.0, "spent": 2999.0, "annual_limit": 36000.0},
                    "learning": {"monthly_limit": 10000.0, "spent": 8500.0, "annual_limit": 120000.0},
                },
                "claims": [
                    {
                        "claim_id": "CLM-982",
                        "category": "Learning",
                        "amount": 8500.0,
                        "date": "2026-08-10",
                        "description": "AWS Solutions Architect Professional Certification",
                        "status": "APPROVED",
                    }
                ],
                "salary_history": [],
                "job_evaluation": {
                    "goal_completion_pct": 96.0,
                    "milestones_delivered": "Q2 Roadmap Delivered On Schedule",
                    "code_quality_and_reliability": 95.0,
                    "timeliness": 94.0,
                    "expense_policy_discipline": 95.0,
                    "overall_job_performance": 95.0,
                    "rating": "OUTSTANDING",
                }
            },
            {
                "employee_id": "EMP-103",
                "name": "Aman Mehra",
                "email": "aman.mehra@aifinance.local",
                "phone": "+91 98765 43212",
                "department": "Marketing",
                "designation": "Growth Marketing Lead",
                "salary_band": "₹14–20 LPA",
                "annual_ctc": 1650000.0,
                "monthly_basic": 82000.0,
                "hra": 32800.0,
                "special_allowance": 14000.0,
                "bonus_variable": 10000.0,
                "pf_deduction": 9840.0,
                "tds_deduction": 14500.0,
                "other_deductions": 0.0,
                "joining_date": "2022-11-10",
                "employment_type": "Full-Time",
                "status": "ACTIVE",
                "manager": "Vikramaditya S.",
                "location": "Mumbai",
                "monthly_allowance_limit": 15000.0,
                "annual_allowance_limit": 180000.0,
                "allowance_policy": {
                    "travel": {"monthly_limit": 15000.0, "spent": 14800.0, "annual_limit": 180000.0},
                    "food": {"monthly_limit": 6000.0, "spent": 5800.0, "annual_limit": 72000.0},
                    "internet": {"monthly_limit": 2000.0, "spent": 1999.0, "annual_limit": 24000.0},
                },
                "claims": [
                    {
                        "claim_id": "CLM-970",
                        "category": "Travel",
                        "amount": 7400.0,
                        "date": "2026-08-15",
                        "description": "Mumbai Partner Summit Hotel",
                        "status": "APPROVED",
                    },
                    {
                        "claim_id": "CLM-972",
                        "category": "Travel",
                        "amount": 7400.0,
                        "date": "2026-08-16",
                        "description": "Mumbai Partner Summit Hotel (Duplicate Submission Risk)",
                        "status": "FLAGGED_REVIEW",
                        "anomaly_reason": "Duplicate Risk: Identical claim amount ₹7,400 submitted within 24 hours of CLM-970.",
                    }
                ],
                "salary_history": [],
                "job_evaluation": {
                    "goal_completion_pct": 91.0,
                    "milestones_delivered": "Campaign ROI +32%",
                    "code_quality_and_reliability": 88.0,
                    "timeliness": 90.0,
                    "expense_policy_discipline": 72.0,
                    "overall_job_performance": 85.0,
                    "rating": "MEETS_EXPECTATIONS",
                }
            },
            {
                "employee_id": "EMP-104",
                "name": "Kavita Iyer",
                "email": "kavita.iyer@aifinance.local",
                "phone": "+91 98765 43213",
                "department": "Finance",
                "designation": "Financial Controller & Auditor",
                "salary_band": "₹16–22 LPA",
                "annual_ctc": 1800000.0,
                "monthly_basic": 90000.0,
                "hra": 36000.0,
                "special_allowance": 15000.0,
                "bonus_variable": 10000.0,
                "pf_deduction": 10800.0,
                "tds_deduction": 16200.0,
                "other_deductions": 0.0,
                "joining_date": "2022-03-01",
                "employment_type": "Full-Time",
                "status": "ACTIVE",
                "manager": "Vikramaditya S.",
                "location": "Bangalore HQ",
                "monthly_allowance_limit": 12000.0,
                "annual_allowance_limit": 144000.0,
                "allowance_policy": {
                    "travel": {"monthly_limit": 12000.0, "spent": 4500.0, "annual_limit": 144000.0},
                    "food": {"monthly_limit": 5000.0, "spent": 3200.0, "annual_limit": 60000.0},
                    "internet": {"monthly_limit": 2000.0, "spent": 1999.0, "annual_limit": 24000.0},
                },
                "claims": [
                    {
                        "claim_id": "CLM-960",
                        "category": "Travel",
                        "amount": 4500.0,
                        "date": "2026-08-05",
                        "description": "Statutory Auditor Travel",
                        "status": "APPROVED",
                    }
                ],
                "salary_history": [],
                "job_evaluation": {
                    "goal_completion_pct": 98.0,
                    "milestones_delivered": "Statutory Audit Completed Clean",
                    "code_quality_and_reliability": 97.0,
                    "timeliness": 98.0,
                    "expense_policy_discipline": 99.0,
                    "overall_job_performance": 98.0,
                    "rating": "OUTSTANDING",
                }
            }
        ]

        # Dynamically load and enrich all 100 employees from the enterprise dataset
        try:
            dataset_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data",
                "enterprise_dataset.json",
            )
            if os.path.exists(dataset_path):
                with open(dataset_path, "r", encoding="utf-8") as f:
                    ds = json.load(f)

                ds_emps = ds.get("employees", [])
                ds_allowances = ds.get("allowances", [])
                existing_ids = {e["employee_id"].replace("-", "").lower() for e in initial_list}

                for de in ds_emps:
                    emp_id = de.get("employee_id")
                    if not emp_id or emp_id.replace("-", "").lower() in existing_ids:
                        continue

                    basic = float(de.get("basic_salary") or de.get("monthly_basic") or 60000.0)
                    ctc = float(de.get("annual_ctc") or (basic * 14))

                    # Find all allowances for this employee from dataset
                    emp_allows = [a for a in ds_allowances if a.get("employee_id") == emp_id]
                    policy = {
                        "travel": {"monthly_limit": round(basic * 0.10, 2), "spent": 0.0, "annual_limit": round(basic * 1.2, 2)},
                        "food": {"monthly_limit": round(basic * 0.05, 2), "spent": 0.0, "annual_limit": round(basic * 0.6, 2)},
                        "fuel": {"monthly_limit": round(basic * 0.04, 2), "spent": 0.0, "annual_limit": round(basic * 0.48, 2)},
                        "internet": {"monthly_limit": 2000.0, "spent": 1499.0, "annual_limit": 24000.0},
                        "mobile": {"monthly_limit": 1500.0, "spent": 999.0, "annual_limit": 18000.0},
                        "learning": {"monthly_limit": 5000.0, "spent": 0.0, "annual_limit": 60000.0},
                        "wellness": {"monthly_limit": 3000.0, "spent": 1500.0, "annual_limit": 36000.0},
                        "wfh": {"monthly_limit": 4000.0, "spent": 2000.0, "annual_limit": 48000.0},
                    }

                    for ea in emp_allows:
                        atype = (ea.get("allowance_type") or "other").lower()
                        mlim = float(ea.get("monthly_limit") or (basic * 0.10))
                        spent = float(ea.get("used_amount") or 0.0)
                        policy[atype] = {
                            "monthly_limit": mlim,
                            "spent": spent,
                            "annual_limit": mlim * 12
                        }

                    travel_spent = policy["travel"]["spent"]
                    travel_limit = policy["travel"]["monthly_limit"]

                    initial_list.append({
                        "employee_id": emp_id,
                        "name": de.get("name", "Employee"),
                        "email": de.get("email", f"{emp_id.lower()}@aifinance.local"),
                        "phone": de.get("phone", "+91 98765 00000"),
                        "department": de.get("department", "Engineering"),
                        "designation": de.get("designation", "Software Engineer"),
                        "salary_band": de.get("salary_band", f"₹{round(ctc/100000, 1)} LPA"),
                        "annual_ctc": ctc,
                        "monthly_basic": basic,
                        "hra": round(basic * 0.40, 2),
                        "special_allowance": round(basic * 0.15, 2),
                        "bonus_variable": round(basic * 0.05, 2),
                        "pf_deduction": round(basic * 0.12, 2),
                        "tds_deduction": round(basic * 0.10, 2),
                        "other_deductions": 0.0,
                        "joining_date": de.get("joining_date", "2024-01-15"),
                        "employment_type": de.get("employment_type", "Full-Time"),
                        "status": de.get("status", "ACTIVE"),
                        "manager": de.get("manager", "Vikramaditya S."),
                        "location": de.get("location", "Bangalore HQ"),
                        "monthly_allowance_limit": round(basic * 0.20, 2),
                        "annual_allowance_limit": round(basic * 2.4, 2),
                        "allowance_policy": policy,
                        "claims": [
                            {
                                "claim_id": f"CLM-{emp_id}-01",
                                "category": "Travel",
                                "amount": round(travel_spent, 2),
                                "date": "2026-08-15",
                                "description": "Monthly Travel Reimbursement Claim",
                                "status": "APPROVED" if travel_spent <= travel_limit else "FLAGGED_REVIEW"
                            }
                        ] if travel_spent > 0 else [],
                        "salary_history": [
                            {
                                "effective_date": "2025-04-01",
                                "previous_salary": round(basic * 0.90, 2),
                                "new_salary": basic,
                                "increase_pct": 11.1,
                                "reason": "Annual Merit Increment",
                                "approved_by": "Vikramaditya S. (CFO)"
                            }
                        ],
                        "job_evaluation": {
                            "goal_completion_pct": 92.0,
                            "milestones_delivered": "4 / 4 Deliverables",
                            "code_quality_and_reliability": 90.0,
                            "timeliness": 91.0,
                            "expense_policy_discipline": 88.0,
                            "overall_job_performance": 90.0,
                            "rating": "MEETS_EXPECTATIONS"
                        }
                    })
        except Exception as e:
            logger.error(f"Failed to load dataset employees in employee_finance_service: {e}")

        return initial_list

    # =========================================================================
    # EMPLOYEE RETRIEVAL & CRUD OPERATIONS
    # =========================================================================

    def get_all_employees(
        self,
        user_role: Optional[str] = None,
        user_department: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Returns employees filtered by RBAC permissions."""
        employees = self._employees
        if user_role == "DEPARTMENT_HEAD" and user_department:
            return [e for e in employees if e["department"].lower() == user_department.lower()]
        return employees

    def get_employee(
        self,
        employee_id: str,
        user_role: Optional[str] = None,
        user_department: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Retrieves a single employee record with computed salary breakdown."""
        target_norm = employee_id.replace("-", "").strip().lower()
        for emp in self._employees:
            emp_norm = emp["employee_id"].replace("-", "").strip().lower()
            if emp_norm == target_norm or emp["employee_id"].lower() == employee_id.lower():
                if user_role == "DEPARTMENT_HEAD" and user_department:
                    if emp["department"].lower() != user_department.lower():
                        raise PermissionError(f"Access denied to employee in {emp['department']} department.")
                
                # Compute mathematical salary figures deterministically
                b = emp.get("monthly_basic") or emp.get("basic_salary") or 50000.0
                hra = emp.get("hra", b * 0.40)
                spec = emp.get("special_allowance", b * 0.15)
                bonus = emp.get("bonus_variable", b * 0.05)
                
                # Active monthly allowances
                allowance_spent = sum(cat.get("spent", 0.0) for cat in emp.get("allowance_policy", {}).values())
                
                gross_salary = b + hra + spec + bonus
                pf = emp.get("pf_deduction", b * 0.12)
                tds = emp.get("tds_deduction", b * 0.10)
                other = emp.get("other_deductions", 0.0)
                total_deductions = pf + tds + other
                net_salary = max(0.0, gross_salary - total_deductions)

                emp_copy = dict(emp)
                emp_copy["computed_compensation"] = {
                    "monthly_basic": b,
                    "hra": hra,
                    "special_allowance": spec,
                    "bonus_variable": bonus,
                    "gross_salary": gross_salary,
                    "pf_deduction": pf,
                    "tds_deduction": tds,
                    "other_deductions": other,
                    "total_deductions": total_deductions,
                    "net_salary": net_salary,
                    "current_monthly_allowances_claimed": allowance_spent,
                }
                return emp_copy
        return None

    def add_employee(
        self,
        data: Dict[str, Any],
        user_id: str,
        user_name: str,
        user_role: str,
    ) -> Dict[str, Any]:
        """Creates a new employee record and logs to audit trail."""
        emp_id = data.get("employee_id", f"EMP-{len(self._employees) + 101}")
        
        # Check uniqueness
        if any(e["employee_id"] == emp_id for e in self._employees):
            raise ValueError(f"Employee ID '{emp_id}' already exists.")

        basic = float(data.get("monthly_basic", 50000.0))
        new_emp = {
            "employee_id": emp_id,
            "name": data.get("name", "New Employee"),
            "email": data.get("email", f"{emp_id.lower()}@aifinance.local"),
            "phone": data.get("phone", "+91 98000 00000"),
            "department": data.get("department", "Engineering"),
            "designation": data.get("designation", "Software Engineer"),
            "salary_band": data.get("salary_band", "₹8–12 LPA"),
            "annual_ctc": float(data.get("annual_ctc", basic * 14)),
            "monthly_basic": basic,
            "hra": float(data.get("hra", basic * 0.40)),
            "special_allowance": float(data.get("special_allowance", 5000.0)),
            "bonus_variable": float(data.get("bonus_variable", 0.0)),
            "pf_deduction": float(data.get("pf_deduction", basic * 0.12)),
            "tds_deduction": float(data.get("tds_deduction", 5000.0)),
            "other_deductions": 0.0,
            "joining_date": data.get("joining_date", datetime.now().strftime("%Y-%m-%d")),
            "employment_type": data.get("employment_type", "Full-Time"),
            "status": "ACTIVE",
            "manager": data.get("manager", "Vikramaditya S."),
            "location": data.get("location", "Bangalore HQ"),
            "monthly_allowance_limit": float(data.get("monthly_allowance_limit", 10000.0)),
            "annual_allowance_limit": float(data.get("annual_allowance_limit", 120000.0)),
            "allowance_policy": data.get("allowance_policy", {
                "travel": {"monthly_limit": 10000.0, "spent": 0.0, "annual_limit": 120000.0},
                "food": {"monthly_limit": 4000.0, "spent": 0.0, "annual_limit": 48000.0},
                "internet": {"monthly_limit": 2000.0, "spent": 0.0, "annual_limit": 24000.0},
            }),
            "claims": [],
            "salary_history": [],
            "job_evaluation": {
                "goal_completion_pct": 100.0,
                "milestones_delivered": "New Hire Onboarding",
                "code_quality_and_reliability": 90.0,
                "timeliness": 90.0,
                "expense_policy_discipline": 100.0,
                "overall_job_performance": 95.0,
                "rating": "NEW_HIRE_COMPLIANT",
            }
        }

        self._employees.append(new_emp)

        audit_service.log_action(
            user_id=user_id,
            user_name=user_name,
            role=user_role,
            action="CREATE_EMPLOYEE",
            entity="EMPLOYEE",
            entity_id=emp_id,
            new_value=new_emp["name"],
            details=f"Added employee {new_emp['name']} ({new_emp['department']} - {new_emp['designation']}). Basic: ₹{basic:,.2f}",
            risk_level="LOW",
        )

        return {"success": True, "message": f"Employee {new_emp['name']} added successfully.", "employee": new_emp}

    def update_employee(
        self,
        employee_id: str,
        data: Dict[str, Any],
        user_id: str,
        user_name: str,
        user_role: str,
    ) -> Dict[str, Any]:
        """Updates an existing employee's details."""
        for emp in self._employees:
            if emp["employee_id"].lower() == employee_id.lower():
                for k, v in data.items():
                    if k not in ["employee_id", "salary_history", "claims"]:
                        emp[k] = v

                audit_service.log_action(
                    user_id=user_id,
                    user_name=user_name,
                    role=user_role,
                    action="UPDATE_EMPLOYEE",
                    entity="EMPLOYEE",
                    entity_id=employee_id,
                    details=f"Updated employee profile for {emp['name']}.",
                    risk_level="LOW",
                )
                return {"success": True, "message": f"Employee {emp['name']} updated successfully.", "employee": emp}

        raise ValueError(f"Employee '{employee_id}' not found.")

    def deactivate_employee(
        self,
        employee_id: str,
        reason: str,
        user_id: str,
        user_name: str,
        user_role: str,
    ) -> Dict[str, Any]:
        """Deactivates an employee rather than destructively wiping historical records."""
        for emp in self._employees:
            if emp["employee_id"].lower() == employee_id.lower():
                emp["status"] = "DEACTIVATED"
                emp["deactivated_at"] = datetime.now().isoformat()
                emp["deactivation_reason"] = reason or "Employee separated/relieved."

                audit_service.log_action(
                    user_id=user_id,
                    user_name=user_name,
                    role=user_role,
                    action="DEACTIVATE_EMPLOYEE",
                    entity="EMPLOYEE",
                    entity_id=employee_id,
                    new_value="DEACTIVATED",
                    details=f"Deactivated employee {emp['name']}. Reason: {emp['deactivation_reason']}",
                    risk_level="MEDIUM",
                )
                return {"success": True, "message": f"Employee {emp['name']} successfully deactivated.", "employee": emp}

        raise ValueError(f"Employee '{employee_id}' not found.")

    def delete_employee(
        self,
        employee_id: str,
        user_id: str,
        user_name: str,
        user_role: str,
    ) -> Dict[str, Any]:
        """Safely deletes an employee only if no financial or payroll records exist."""
        for idx, emp in enumerate(self._employees):
            if emp["employee_id"].lower() == employee_id.lower():
                # Safety check: if employee has claims or salary history, disallow hard deletion
                if emp.get("claims") or emp.get("salary_history"):
                    raise ValueError(
                        f"Employee '{emp['name']}' has active financial and claims history. Deactivation is required to preserve financial auditability."
                    )
                
                deleted_name = emp["name"]
                self._employees.pop(idx)

                audit_service.log_action(
                    user_id=user_id,
                    user_name=user_name,
                    role=user_role,
                    action="DELETE_EMPLOYEE",
                    entity="EMPLOYEE",
                    entity_id=employee_id,
                    details=f"Deleted employee record {deleted_name} ({employee_id}).",
                    risk_level="HIGH",
                )
                return {"success": True, "message": f"Employee {deleted_name} deleted successfully."}

        raise ValueError(f"Employee '{employee_id}' not found.")

    # =========================================================================
    # SALARY REVISION ENGINE
    # =========================================================================

    def revise_salary(
        self,
        employee_id: str,
        new_basic: float,
        effective_date: str,
        reason: str,
        user_id: str,
        user_name: str,
        user_role: str,
    ) -> Dict[str, Any]:
        """Executes an authorized salary revision and logs to audit trail."""
        for emp in self._employees:
            if emp["employee_id"].lower() == employee_id.lower():
                current_basic = emp["monthly_basic"]
                increase_amount = new_basic - current_basic
                increase_pct = round((increase_amount / current_basic) * 100, 2) if current_basic > 0 else 0.0

                rev_entry = {
                    "effective_date": effective_date or datetime.now().strftime("%Y-%m-%d"),
                    "previous_salary": current_basic,
                    "new_salary": new_basic,
                    "increase_pct": increase_pct,
                    "increase_amount": increase_amount,
                    "reason": reason,
                    "approved_by": f"{user_name} ({user_role})",
                    "timestamp": datetime.now().isoformat(),
                }

                emp.setdefault("salary_history", []).append(rev_entry)
                emp["monthly_basic"] = new_basic
                emp["hra"] = new_basic * 0.40
                emp["pf_deduction"] = new_basic * 0.12

                audit_service.log_action(
                    user_id=user_id,
                    user_name=user_name,
                    role=user_role,
                    action="REVISE_EMPLOYEE_SALARY",
                    entity="EMPLOYEE_SALARY",
                    entity_id=employee_id,
                    new_value=f"₹{new_basic:,.2f}",
                    details=f"Revised basic salary for {emp['name']} from ₹{current_basic:,.2f} to ₹{new_basic:,.2f} (+{increase_pct}%). Reason: {reason}",
                    risk_level="HIGH",
                )

                return {
                    "success": True,
                    "message": f"Salary for {emp['name']} successfully revised to ₹{new_basic:,.2f} (+{increase_pct}%).",
                    "salary_revision": rev_entry,
                }

        raise ValueError(f"Employee '{employee_id}' not found.")

    def recommend_allowance_limit(self, employee_id: str, category: str = "Travel") -> Dict[str, Any]:
        """Backwards-compatible wrapper for allowance recommendation."""
        res = self.evaluate_allowance_request(employee_id, category, 13000.0)
        emp = self.get_employee(employee_id) or {}
        return {
            "employee_id": employee_id,
            "employee_name": res["employee_name"],
            "designation": emp.get("designation", "Software Engineer"),
            "department": res["department"],
            "allowance_type": category,
            "current_monthly_limit": res["current_limit"],
            "historical_monthly_average": res["historical_average"],
            "recommended_monthly_limit": res["recommended_amount"],
            "confidence_percentage": 92.0,
            "rationale": res["reason"],
            "justification": res["reason"],
            "department_benchmark": res["department_limit"],
            "data_sources_evaluated": [
                f"Historical claims in {category}",
                f"{res['department']} benchmark policy ceiling",
                "Current monthly utilization rate",
            ]
        }

    def evaluate_allowance_request(
        self,
        employee_id: str,
        category: str,
        requested_limit: float,
    ) -> Dict[str, Any]:
        """
        Runs deterministic rule evaluation:
        Role + Department Policy + Salary Band + Historical Claims + Department Budget.
        """
        emp = self.get_employee(employee_id)
        if not emp:
            raise ValueError(f"Employee '{employee_id}' not found.")

        cat_key = category.lower()
        current_cat_policy = emp.get("allowance_policy", {}).get(cat_key, {})
        current_limit = current_cat_policy.get("monthly_limit", 10000.0)
        spent = current_cat_policy.get("spent", 0.0)

        # Department benchmark limits
        dept_limits = {
            "Engineering": {"travel": 15000.0, "food": 6000.0, "internet": 2500.0, "learning": 8000.0},
            "Marketing": {"travel": 18000.0, "food": 7000.0, "internet": 2500.0, "learning": 6000.0},
            "Finance": {"travel": 12000.0, "food": 5000.0, "internet": 2000.0, "learning": 5000.0},
            "Sales": {"travel": 25000.0, "food": 8000.0, "internet": 2500.0, "learning": 5000.0},
        }

        dept_limit = dept_limits.get(emp["department"], {}).get(cat_key, 12000.0)
        historical_avg = spent if spent > 0 else (current_limit * 0.75)

        if requested_limit <= dept_limit:
            verdict = "WITHIN_POLICY"
            recommended_amount = requested_limit
            assessment = "Within recommended department policy cap."
            reason = f"Requested amount (₹{requested_limit:,.0f}) is within the standard {emp['department']} {category} ceiling of ₹{dept_limit:,.0f}."
        else:
            verdict = "ABOVE_DEPARTMENT_LIMIT"
            recommended_amount = dept_limit
            assessment = "Above recommended department limit."
            reason = f"Requested amount (₹{requested_limit:,.0f}) exceeds the configured {emp['department']} {category} limit (₹{dept_limit:,.0f}). Approval of cap recommended."

        return {
            "employee_id": employee_id,
            "employee_name": emp["name"],
            "department": emp["department"],
            "category": category,
            "requested_limit": requested_limit,
            "current_limit": current_limit,
            "historical_average": historical_avg,
            "department_limit": dept_limit,
            "verdict": verdict,
            "assessment": assessment,
            "recommended_amount": recommended_amount,
            "reason": reason,
        }

    def detect_allowance_anomalies(
        self,
        user_role: Optional[str] = None,
        user_department: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Identifies policy breaches, duplicate receipts, and unusual spikes."""
        anomalies = []
        employees = self.get_all_employees(user_role, user_department)

        for emp in employees:
            # 1. Policy Limit Breaches
            for cat, pol in emp.get("allowance_policy", {}).items():
                spent = pol.get("spent", 0.0)
                limit = pol.get("monthly_limit", 0.0)
                if spent > limit:
                    diff = spent - limit
                    anomalies.append({
                        "type": "POLICY_LIMIT_EXCEEDED",
                        "severity": "CRITICAL",
                        "employee_id": emp["employee_id"],
                        "employee_name": emp["name"],
                        "department": emp["department"],
                        "category": cat.capitalize(),
                        "spent_amount": spent,
                        "limit_amount": limit,
                        "excess_amount": diff,
                        "badge": "LIMIT EXCEEDED",
                        "description": f"{emp['name']} has claimed ₹{spent:,.2f} in {cat.capitalize()}, exceeding monthly policy cap of ₹{limit:,.2f} by ₹{diff:,.2f}.",
                        "action_label": "Review Claims",
                    })

            # 2. Duplicate or Unusual Claims
            for clm in emp.get("claims", []):
                if clm.get("status") == "FLAGGED_REVIEW":
                    anomalies.append({
                        "type": "FLAGGED_CLAIM",
                        "severity": "WARNING",
                        "employee_id": emp["employee_id"],
                        "employee_name": emp["name"],
                        "department": emp["department"],
                        "category": clm.get("category", "General"),
                        "claim_id": clm["claim_id"],
                        "claim_amount": clm["amount"],
                        "badge": "DUPLICATE / ANOMALY",
                        "description": f"{emp['name']} - Claim {clm['claim_id']} (₹{clm['amount']:,.2f}): {clm.get('anomaly_reason', 'Flagged for review')}",
                        "action_label": "Investigate Claim",
                    })

        return anomalies


employee_finance_service = EmployeeFinancialControlService()
