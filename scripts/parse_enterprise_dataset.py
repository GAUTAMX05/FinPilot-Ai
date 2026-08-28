import os
import csv
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "src" / "app" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CSV_FILE = DATA_DIR / "enterprise_dataset.csv"

def parse_and_build_dataset():
    if not CSV_FILE.exists():
        print(f"Error: {CSV_FILE} does not exist.")
        return

    departments = []
    employees = []
    budgets = []
    spending = []
    vendors = []
    invoices = []
    transactions = []
    allowances = []
    payrolls = []
    form16_records = []
    approvals = []
    notifications = []
    decisions = []

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rtype = row.get("record_type", "").strip().lower()
            
            if rtype == "department":
                departments.append({
                    "id": row.get("record_id"),
                    "name": row.get("name") or row.get("department"),
                    "annual_budget": float(row.get("annual_budget") or 0.0),
                })
            elif rtype == "employee":
                employees.append({
                    "employee_id": row.get("record_id"),
                    "name": row.get("name"),
                    "email": row.get("email"),
                    "department": row.get("department"),
                    "designation": row.get("designation"),
                    "joining_date": row.get("date"),
                    "basic_salary": float(row.get("basic_salary") or 0.0),
                })
            elif rtype == "budget":
                budgets.append({
                    "id": row.get("record_id"),
                    "department_id": row.get("department_id"),
                    "department": row.get("department"),
                    "date": row.get("date"),
                    "monthly_budget": float(row.get("monthly_budget") or 0.0),
                })
            elif rtype == "spending":
                spending.append({
                    "id": row.get("record_id"),
                    "department_id": row.get("department_id"),
                    "department": row.get("department"),
                    "date": row.get("date"),
                    "actual_spend": float(row.get("actual_spend") or 0.0),
                })
            elif rtype == "vendor":
                vendors.append({
                    "vendor_id": row.get("vendor_id") or row.get("record_id"),
                    "vendor_name": row.get("vendor_name"),
                    "category": row.get("category"),
                })
            elif rtype == "invoice":
                invoices.append({
                    "invoice_id": row.get("invoice_id") or row.get("record_id"),
                    "department_id": row.get("department_id"),
                    "department": row.get("department"),
                    "date": row.get("date"),
                    "status": row.get("status"),
                    "amount": float(row.get("amount") or 0.0),
                    "vendor_id": row.get("vendor_id"),
                    "vendor_name": row.get("vendor_name"),
                    "purchase_order": row.get("purchase_order"),
                    "gst_rate": float(row.get("gst_rate") or 0.0),
                    "gst_amount": float(row.get("gst_amount") or 0.0),
                    "total_amount": float(row.get("amount") or 0.0),
                    "subtotal": round(float(row.get("amount") or 0.0) / (1.0 + (float(row.get("gst_rate") or 0.0)/100.0)), 2),
                })
            elif rtype == "transaction":
                transactions.append({
                    "transaction_id": row.get("transaction_id") or row.get("record_id"),
                    "department_id": row.get("department_id"),
                    "department": row.get("department"),
                    "date": row.get("date"),
                    "type": row.get("type"),
                    "status": row.get("status"),
                    "amount": float(row.get("amount") or 0.0),
                    "gateway_reference": row.get("gateway_reference"),
                    "direction": row.get("direction"),
                })
            elif rtype == "allowance":
                allowances.append({
                    "employee_id": row.get("record_id"),
                    "name": row.get("name"),
                    "department": row.get("department"),
                    "designation": row.get("designation"),
                    "allowance_type": row.get("allowance_type") or row.get("category"),
                    "status": row.get("status"),
                    "monthly_limit": float(row.get("monthly_limit") or 0.0),
                    "used_amount": float(row.get("used_amount") or 0.0),
                    "remaining_amount": float(row.get("remaining_amount") or 0.0),
                })
            elif rtype == "payroll":
                payrolls.append({
                    "payroll_id": row.get("record_id"),
                    "employee_id": row.get("parent_id") or row.get("record_id").split("-")[1] if "-" in row.get("record_id", "") else "",
                    "name": row.get("name"),
                    "department": row.get("department"),
                    "period": row.get("period"),
                    "basic_salary": float(row.get("basic_salary") or 0.0),
                    "hra": float(row.get("hra") or 0.0),
                    "other_allowances": float(row.get("other_allowances") or 0.0),
                    "gross_salary": float(row.get("gross_salary") or 0.0),
                    "tds": float(row.get("tds") or 0.0),
                    "other_deductions": float(row.get("other_deductions") or 0.0),
                    "net_salary": float(row.get("net_salary") or 0.0),
                })
            elif rtype == "form16":
                form16_records.append({
                    "form16_id": row.get("record_id"),
                    "name": row.get("name"),
                    "department": row.get("department"),
                    "status": row.get("status"),
                    "tds": float(row.get("tds") or 0.0),
                    "reported_salary": float(row.get("reported_salary") or 0.0),
                    "reported_tds": float(row.get("reported_tds") or 0.0),
                    "difference": float(row.get("difference") or 0.0),
                })
            elif rtype == "approval":
                approvals.append({
                    "approval_id": row.get("record_id"),
                    "department": row.get("department"),
                    "type": row.get("type"),
                    "status": row.get("status"),
                    "amount": float(row.get("amount") or 0.0),
                    "approver_role": row.get("approver_role"),
                })
            elif rtype == "notification":
                notifications.append({
                    "notification_id": row.get("record_id"),
                    "type": row.get("type"),
                    "priority": row.get("priority"),
                    "recipient_user_id": row.get("recipient_user_id"),
                    "sender_user_id": row.get("sender_user_id"),
                    "sender_role": row.get("sender_role"),
                    "recipient_role": row.get("recipient_role"),
                    "message": row.get("message"),
                })
            elif rtype == "decision":
                decisions.append({
                    "decision_id": row.get("record_id"),
                    "priority": row.get("priority"),
                    "amount": float(row.get("amount") or 0.0),
                    "category": row.get("category"),
                    "check": row.get("check"),
                    "result": row.get("result"),
                    "reason": row.get("reason"),
                    "recommended_action": row.get("recommended_action"),
                })

    dataset = {
        "departments": departments,
        "employees": employees,
        "budgets": budgets,
        "spending": spending,
        "vendors": vendors,
        "invoices": invoices,
        "transactions": transactions,
        "allowances": allowances,
        "payrolls": payrolls,
        "form16": form16_records,
        "approvals": approvals,
        "notifications": notifications,
        "decisions": decisions,
    }

    out_json = DATA_DIR / "enterprise_dataset.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    # Also update sample_invoices.json
    out_invoices = DATA_DIR / "sample_invoices.json"
    with open(out_invoices, "w", encoding="utf-8") as f:
        json.dump(invoices, f, indent=2)

    print(f"Dataset compiled successfully into {out_json}:")
    print(f"  Departments: {len(departments)}")
    print(f"  Employees: {len(employees)}")
    print(f"  Budgets: {len(budgets)}")
    print(f"  Spending: {len(spending)}")
    print(f"  Vendors: {len(vendors)}")
    print(f"  Invoices: {len(invoices)}")
    print(f"  Transactions: {len(transactions)}")
    print(f"  Allowances: {len(allowances)}")
    print(f"  Payrolls: {len(payrolls)}")
    print(f"  Form 16 Records: {len(form16_records)}")
    print(f"  Approvals: {len(approvals)}")
    print(f"  Notifications: {len(notifications)}")
    print(f"  Decisions: {len(decisions)}")

if __name__ == "__main__":
    parse_and_build_dataset()
