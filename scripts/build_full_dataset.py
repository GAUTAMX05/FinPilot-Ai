import os
import json
import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "src" / "app" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CSV_FILE = DATA_DIR / "enterprise_dataset.csv"

# Let's append budgets, spending, vendors, invoices, transactions, allowances, payrolls, form16, approvals, notifications, decisions
def build_full_dataset():
    # Let's read existing lines (header + departments + employees)
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        existing_content = f.read()

    # Now let's append the remaining sections
    append_lines = []

    # 1. Budgets
    dept_map = {
        "D001": ("Engineering", 3500000.0, 291666.67),
        "D002": ("Marketing", 2800000.0, 233333.33),
        "D003": ("Sales", 3000000.0, 250000.0),
        "D004": ("Operations", 2700000.0, 225000.0),
        "D005": ("HR", 2000000.0, 166666.67),
    }
    months = ["2026-04-01", "2026-05-01", "2026-06-01", "2026-07-01", "2026-08-01"]
    spending_matrix = {
        "D001": [269800.03, 298032.49, 283003.28, 365083.29, 388358.04],
        "D002": [223973.58, 229987.63, 242873.91, 223208.46, 256697.89],
        "D003": [241590.06, 236448.85, 267187.91, 262324.82, 255336.15],
        "D004": [238372.58, 235932.19, 213716.52, 239132.12, 226416.32],
        "D005": [174865.07, 177229.10, 161813.43, 156268.05, 159411.60],
    }

    for did, (dname, ann, mb) in dept_map.items():
        for m in months:
            mid = m.replace("-", "")[:6]
            append_lines.append(f"budget,{did}-{mid},,,, {did},{dname},,{m},,,,,,,,,,,{mb},,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,")
            
    for did, (dname, ann, mb) in dept_map.items():
        for idx, m in enumerate(months):
            mid = m.replace("-", "")[:6]
            sp = spending_matrix[did][idx]
            append_lines.append(f"spending,SP-{did}-{mid},,,,{did},{dname},,{m},,,,,,,,,,,,{sp},,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,")

    # 2. Vendors
    vendors = [
        ("VEN001", "CloudOps Technologies Pvt Ltd", "Operations"),
        ("VEN002", "OfficeHub India Pvt Ltd", "Operations"),
        ("VEN003", "AdGrowth Media Pvt Ltd", "Operations"),
        ("VEN004", "SecureNet Systems", "Marketing"),
        ("VEN005", "TalentBridge Services", "HR"),
        ("VEN006", "TravelSphere Corporate", "Marketing"),
        ("VEN007", "DataStack Solutions", "Finance"),
        ("VEN008", "BrightPrint Solutions", "HR"),
        ("VEN009", "Razorpay Services", "Technology"),
        ("VEN010", "NetConnect India", "Operations"),
        ("VEN011", "Insight Consulting", "HR"),
        ("VEN012", "WorkSpace One", "Finance"),
    ]
    for vid, vname, vcat in vendors:
        append_lines.append(f"vendor,{vid},,,,,,,,,{vcat},,,,,,,,,,,,,,,,,,,,,{vid},{vname},,,,,,,,,,,,,,,,,,,,")

    with open(CSV_FILE, "w", encoding="utf-8") as f:
        f.write(existing_content.strip() + "\n" + "\n".join(append_lines) + "\n")

    print(f"Base sections updated in {CSV_FILE}")

if __name__ == "__main__":
    build_full_dataset()
