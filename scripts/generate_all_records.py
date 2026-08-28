import json
import random
from pathlib import Path
from datetime import datetime, timedelta

DATA_DIR = Path(__file__).resolve().parent.parent / "src" / "app" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def generate_complete_enterprise_json():
    # 1. Departments
    departments = [
        {"id": "D001", "name": "Engineering", "annual_budget": 3500000.0, "monthly_budget": 291666.67},
        {"id": "D002", "name": "Marketing", "annual_budget": 2800000.0, "monthly_budget": 233333.33},
        {"id": "D003", "name": "Sales", "annual_budget": 3000000.0, "monthly_budget": 250000.0},
        {"id": "D004", "name": "Operations", "annual_budget": 2700000.0, "monthly_budget": 225000.0},
        {"id": "D005", "name": "HR", "annual_budget": 2000000.0, "monthly_budget": 166666.67},
    ]

    # 2. Vendors
    vendors = [
        {"vendor_id": "VEN001", "vendor_name": "CloudOps Technologies Pvt Ltd", "category": "Operations"},
        {"vendor_id": "VEN002", "vendor_name": "OfficeHub India Pvt Ltd", "category": "Operations"},
        {"vendor_id": "VEN003", "vendor_name": "AdGrowth Media Pvt Ltd", "category": "Marketing"},
        {"vendor_id": "VEN004", "vendor_name": "SecureNet Systems", "category": "Security"},
        {"vendor_id": "VEN005", "vendor_name": "TalentBridge Services", "category": "HR"},
        {"vendor_id": "VEN006", "vendor_name": "TravelSphere Corporate", "category": "Travel"},
        {"vendor_id": "VEN007", "vendor_name": "DataStack Solutions", "category": "Technology"},
        {"vendor_id": "VEN008", "vendor_name": "BrightPrint Solutions", "category": "Office"},
        {"vendor_id": "VEN009", "vendor_name": "Razorpay Services", "category": "Fintech"},
        {"vendor_id": "VEN010", "vendor_name": "NetConnect India", "category": "Infrastructure"},
        {"vendor_id": "VEN011", "vendor_name": "Insight Consulting", "category": "Consulting"},
        {"vendor_id": "VEN012", "vendor_name": "WorkSpace One", "category": "Facilities"},
    ]

    # 3. Monthly Budgets & Spending
    months = ["2026-04", "2026-05", "2026-06", "2026-07", "2026-08"]
    spending_matrix = {
        "D001": [269800.03, 298032.49, 283003.28, 365083.29, 388358.04],
        "D002": [223973.58, 229987.63, 242873.91, 223208.46, 256697.89],
        "D003": [241590.06, 236448.85, 267187.91, 262324.82, 255336.15],
        "D004": [238372.58, 235932.19, 213716.52, 239132.12, 226416.32],
        "D005": [174865.07, 177229.10, 161813.43, 156268.05, 159411.60],
    }

    budgets = []
    spending = []
    for d in departments:
        for idx, m in enumerate(months):
            budgets.append({
                "id": f"{d['id']}-{m.replace('-', '')}",
                "department_id": d["id"],
                "department": d["name"],
                "month": m,
                "monthly_budget": d["monthly_budget"],
            })
            spending.append({
                "id": f"SP-{d['id']}-{m.replace('-', '')}",
                "department_id": d["id"],
                "department": d["name"],
                "month": m,
                "actual_spend": spending_matrix[d["id"]][idx],
            })

    # 4. 100 Employees from the user prompt
    first_names = ["Rahul", "Arjun", "Vivaan", "Kavya", "Riya", "Aditya", "Diya", "Aditi", "Ishaan", "Vikram", 
                   "Ananya", "Sara", "Kunal", "Meera", "Rohan", "Ira", "Tanya", "Nisha", "Aarav", "Kabir"]
    last_names = ["Sethi", "Nair", "Sharma", "Arora", "Singh", "Malhotra", "Goyal", "Jain", "Kapoor", "Patel",
                  "Bansal", "Verma", "Agarwal", "Mishra", "Khanna", "Chauhan", "Joshi", "Mehta", "Reddy", "Gupta"]
    designations = ["Software Engineer", "Senior Software Engineer", "Product Manager", "Engineering Manager",
                    "Data Analyst", "Finance Executive", "HR Executive", "Operations Analyst", "Marketing Executive", "Sales Executive"]
    
    dept_names = ["Engineering", "Marketing", "Sales", "Operations", "HR"]
    random.seed(42)

    employees = []
    allowances = []
    payrolls = []
    form16_records = []

    for i in range(1, 101):
        emp_id = f"EMP{i:04d}"
        fn = first_names[(i * 7) % len(first_names)]
        ln = last_names[(i * 11) % len(last_names)]
        name = f"{fn} {ln}"
        dept = dept_names[(i * 3) % len(dept_names)]
        desig = designations[(i * 5) % len(designations)]
        
        # Base salary range between 50,000 and 165,000
        base_sal = round(50000.0 + ((i * 1373) % 115000), 2)
        hra = round(base_sal * 0.20, 2)
        other_allow = round(base_sal * 0.10, 2)
        gross = round(base_sal + hra + other_allow, 2)
        tds = round(gross * 0.08, 2)
        pf = round(base_sal * 0.12, 2)
        other_ded = round(pf * 0.35, 2)
        net = round(gross - tds - other_ded, 2)

        joining_date = (datetime(2024, 1, 1) + timedelta(days=(i * 19) % 850)).strftime("%Y-%m-%d")

        employees.append({
            "employee_id": emp_id,
            "name": name,
            "email": f"{fn.lower()}.{ln.lower()}@aifinance.local",
            "department": dept,
            "designation": desig,
            "joining_date": joining_date,
            "basic_salary": base_sal,
            "annual_ctc": round(gross * 12, 2),
            "status": "ACTIVE"
        })

        # Allowances (Travel & Food)
        travel_limit = round(base_sal * 0.10, 2)
        travel_used = round(travel_limit * (0.6 + ((i * 3) % 55) / 100.0), 2)
        travel_exceeded = travel_used > travel_limit
        travel_rem = 0.0 if travel_exceeded else round(travel_limit - travel_used, 2)

        allowances.append({
            "employee_id": emp_id,
            "name": name,
            "department": dept,
            "designation": desig,
            "allowance_type": "Travel",
            "status": "Exceeded" if travel_exceeded else "Within Limit",
            "monthly_limit": travel_limit,
            "used_amount": travel_used,
            "remaining_amount": travel_rem,
        })

        food_limit = round(base_sal * 0.05, 2)
        food_used = round(food_limit * (0.5 + ((i * 7) % 60) / 100.0), 2)
        food_exceeded = food_used > food_limit
        food_rem = 0.0 if food_exceeded else round(food_limit - food_used, 2)

        allowances.append({
            "employee_id": emp_id,
            "name": name,
            "department": dept,
            "designation": desig,
            "allowance_type": "Food",
            "status": "Exceeded" if food_exceeded else "Within Limit",
            "monthly_limit": food_limit,
            "used_amount": food_used,
            "remaining_amount": food_rem,
        })

        # Payroll (August 2026)
        payrolls.append({
            "payroll_id": f"PAY-{emp_id}-202608",
            "employee_id": emp_id,
            "name": name,
            "department": dept,
            "period": "2026-08",
            "basic_salary": base_sal,
            "hra": hra,
            "other_allowances": other_allow,
            "gross_salary": gross,
            "tds": tds,
            "other_deductions": other_ded,
            "net_salary": net,
        })

        # Form 16 record
        is_mismatch = (i in [12, 21, 37, 55, 64, 79, 88, 95])
        rep_sal = gross * 12
        diff = 0.0
        status = "Matched"
        if is_mismatch:
            if i % 2 == 0:
                diff = round(random.choice([18000.0, 35000.0, 42000.0]), 2)
                rep_sal += diff
                status = "Salary Mismatch"
            else:
                status = "TDS Mismatch"

        form16_records.append({
            "form16_id": f"F16-{emp_id}-2025-26",
            "employee_id": emp_id,
            "name": name,
            "department": dept,
            "status": status,
            "tds": round(tds * 12, 2),
            "reported_salary": round(rep_sal, 2),
            "reported_tds": round((tds * 12) + (12000.0 if status == "TDS Mismatch" else 0.0), 2),
            "difference": diff,
        })

    # 5. Invoices (220 Invoices across Apr - Aug 2026)
    invoices = []
    inv_statuses = ["Paid", "Approved", "Pending Review"]
    gst_rates = [5.0, 12.0, 18.0]
    
    start_date = datetime(2026, 4, 1)
    for i in range(1, 221):
        inv_id = f"INV-2026-{i:04d}"
        v = vendors[(i * 3) % len(vendors)]
        dept = dept_names[(i * 7) % len(dept_names)]
        amt = round(12000.0 + ((i * 1789) % 215000), 2)
        gst_r = gst_rates[(i * 2) % len(gst_rates)]
        subtotal = round(amt / (1.0 + (gst_r / 100.0)), 2)
        gst_amt = round(amt - subtotal, 2)
        st = inv_statuses[(i * 5) % len(inv_statuses)]
        inv_date = (start_date + timedelta(days=(i * 1.6) % 150)).strftime("%Y-%m-%d")
        po = f"PO-{((i * 9871) % 90000) + 10000}"

        invoices.append({
            "invoice_id": inv_id,
            "department": dept,
            "date": inv_date,
            "status": st,
            "amount": amt,
            "vendor_id": v["vendor_id"],
            "vendor_name": v["vendor_name"],
            "purchase_order": po,
            "gst_rate": gst_r,
            "gst_amount": gst_amt,
            "subtotal": subtotal,
            "total_amount": amt,
            "category": v["category"]
        })

    # 6. Transactions (500 Transactions across Apr - Aug 2026)
    transactions = []
    txn_types = ["Razorpay Settlement", "Vendor Payment", "Expense", "Refund"]
    txn_statuses = ["Completed", "Pending", "Exception"]

    for i in range(1, 501):
        txn_id = f"TXN-{i:06d}"
        dept = dept_names[(i * 3) % len(dept_names)]
        t_type = txn_types[(i * 7) % len(txn_types)]
        direction = "Inflow" if t_type == "Razorpay Settlement" else "Outflow"
        st = txn_statuses[(i * 11) % len(txn_statuses)]
        amt = round(3500.0 + ((i * 1327) % 198000), 2)
        t_date = (start_date + timedelta(days=(i * 0.3) % 150)).strftime("%Y-%m-%d")
        rzp_ref = f"RZP-{((i * 7731) % 900000) + 100000}"

        transactions.append({
            "transaction_id": txn_id,
            "department": dept,
            "date": t_date,
            "type": t_type,
            "status": st,
            "amount": amt,
            "gateway_reference": rzp_ref,
            "direction": direction
        })

    # 7. Approvals, Notifications, Decisions
    approvals = [
        {"approval_id": "APR-0001", "department": "Engineering", "type": "Expense", "status": "Pending", "amount": 85000.0, "approver_role": "Finance Manager"},
        {"approval_id": "APR-0002", "department": "Engineering", "type": "Budget Increase", "status": "Pending", "amount": 200000.0, "approver_role": "CFO"},
        {"approval_id": "APR-0003", "department": "Operations", "type": "Vendor Payment", "status": "Approved", "amount": 125000.0, "approver_role": "Finance Manager"},
        {"approval_id": "APR-0004", "department": "Engineering", "type": "Salary Revision", "status": "Pending", "amount": 12000.0, "approver_role": "CFO"},
        {"approval_id": "APR-0005", "department": "Sales", "type": "Allowance Exception", "status": "Pending", "amount": 18000.0, "approver_role": "Finance Manager"},
        {"approval_id": "APR-0006", "department": "Marketing", "type": "Invoice Review", "status": "Pending", "amount": 100300.0, "approver_role": "Auditor"},
    ]

    notifications = [
        {"notification_id": "NTF-0001", "type": "APPROVAL_REQUEST", "priority": "HIGH", "recipient_user_id": "CFO-001", "sender_user_id": "FIN-MGR-001", "sender_role": "Finance Manager", "recipient_role": "CFO", "message": "Review ₹85,000 Engineering expense"},
        {"notification_id": "NTF-0002", "type": "DECISION_REQUEST", "priority": "MEDIUM", "recipient_user_id": "FIN-MGR-001", "sender_user_id": "ENG-HEAD-001", "sender_role": "Department Head", "recipient_role": "Finance Manager", "message": "Please justify additional cloud expense"},
        {"notification_id": "NTF-0003", "type": "FORM16_MISMATCH", "priority": "HIGH", "recipient_user_id": "AUDITOR-001", "sender_user_id": "FIN-MGR-001", "sender_role": "Finance Manager", "recipient_role": "Auditor", "message": "5 Form 16 records require review"},
        {"notification_id": "NTF-0004", "type": "BUDGET_WARNING", "priority": "HIGH", "recipient_user_id": "CFO-001", "sender_user_id": "FIN-MGR-001", "sender_role": "Finance Manager", "recipient_role": "CFO", "message": "Projected overrun requires review"},
        {"notification_id": "NTF-0005", "type": "ALLOWANCE_EXCEPTION", "priority": "MEDIUM", "recipient_user_id": "FIN-MGR-001", "sender_user_id": "FIN-MGR-001", "sender_role": "System", "recipient_role": "Finance Manager", "message": "8 employee allowance claims exceed limits"},
    ]

    decisions = [
        {"decision_id": "DEC-001", "priority": "HIGH", "amount": 85000.0, "category": "Expense", "check": "Budget Check", "result": "PASS", "reason": "Budget available but utilization is elevated", "recommended_action": "Review before approval"},
        {"decision_id": "DEC-002", "priority": "CRITICAL", "amount": 420000.0, "category": "Budget", "check": "Forecast", "result": "FAIL", "reason": "Projected year-end spend exceeds allocation", "recommended_action": "Escalate to CFO"},
        {"decision_id": "DEC-003", "priority": "HIGH", "amount": 100300.0, "category": "Invoice", "check": "Duplicate Check", "result": "REVIEW", "reason": "Possible duplicate invoice detected", "recommended_action": "Manual verification"},
        {"decision_id": "DEC-004", "priority": "HIGH", "amount": 35000.0, "category": "Payroll", "check": "Form 16 Reconciliation", "result": "FAIL", "reason": "Reported salary differs from payroll record", "recommended_action": "Review payroll components"},
        {"decision_id": "DEC-005", "priority": "MEDIUM", "amount": 18400.0, "category": "Allowance", "check": "Policy Check", "result": "FAIL", "reason": "Travel claims exceed monthly allowance", "recommended_action": "Review exception"},
    ]

    master_data = {
        "departments": departments,
        "vendors": vendors,
        "budgets": budgets,
        "spending": spending,
        "employees": employees,
        "allowances": allowances,
        "payrolls": payrolls,
        "form16": form16_records,
        "invoices": invoices,
        "transactions": transactions,
        "approvals": approvals,
        "notifications": notifications,
        "decisions": decisions
    }

    out_file = DATA_DIR / "enterprise_dataset.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(master_data, f, indent=2)

    # Update sample_invoices.json
    with open(DATA_DIR / "sample_invoices.json", "w", encoding="utf-8") as f:
        json.dump(invoices, f, indent=2)

    print(f"Generated complete enterprise dataset with:")
    print(f"  {len(departments)} Departments")
    print(f"  {len(vendors)} Vendors")
    print(f"  {len(employees)} Employees")
    print(f"  {len(invoices)} Invoices")
    print(f"  {len(transactions)} Transactions")
    print(f"  {len(allowances)} Allowances")
    print(f"  {len(payrolls)} Payroll Records")
    print(f"  {len(form16_records)} Form 16 Records")

if __name__ == "__main__":
    generate_complete_enterprise_json()
