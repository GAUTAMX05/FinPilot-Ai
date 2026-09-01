# -*- coding: utf-8 -*-
"""
FinPilot AI — Autonomous Finance Controller Benchmark CLI
=========================================================
Executes a reproducible, deterministic 3-way reconciliation run against the
120-record financial benchmark dataset, computes exact accuracy, precision,
recall, F1-score, and throughput vs ground truth, and outputs machine-readable
JSON and a human-readable scorecard.

Usage:
    python -m src.app.benchmarks.run_controller
    python -m benchmarks.run_controller
"""

import sys
import os
import json
import time

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure repository root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
while current_dir and not os.path.exists(os.path.join(current_dir, "src", "app")):
    parent = os.path.dirname(current_dir)
    if parent == current_dir:
        break
    current_dir = parent

if current_dir and current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.app.core.database import init_db
from src.app.services.finance_controller_service import finance_controller_service


def run_benchmark(output_json_path: str = None) -> int:
    print("=" * 72)
    print("   FINPILOT AI -- AUTONOMOUS FINANCE CONTROLLER BENCHMARK EVALUATION   ")
    print("=" * 72)

    print("\n[1/3] Initializing SQLite database and verifying benchmark dataset...")
    init_db()

    print("[2/3] Executing deterministic 3-way reconciliation pipeline...")
    start = time.perf_counter()
    run_res = finance_controller_service.run_close_month(actor="Benchmark CLI")
    duration_ms = round((time.perf_counter() - start) * 1000, 2)

    print(f"      - Run ID: {run_res['run_id']}")
    print(f"      - Records Processed: {run_res['records_processed']}")
    print(f"      - Matched Records: {run_res['auto_reconciled']} ({run_res['match_rate_percentage']}%)")
    print(f"      - Detected Exceptions: {run_res['exceptions_count']}")
    print(f"      - Processing Latency: {run_res['duration_ms']} ms")
    print(f"      - Throughput: {run_res['throughput_rps']:,.1f} records/sec")

    print("\n[3/3] Evaluating reconciliation against internal ground truth...")
    eval_res = finance_controller_service.evaluate_benchmark(run_id=run_res["run_id"])

    print("\n" + "=" * 72)
    print("   BENCHMARK SCORECARD VS GROUND TRUTH (120 RECORDS)                 ")
    print("=" * 72)
    print(f"  Total Evaluated Records:       {eval_res['total_records']}")
    print(f"  Correct Match Classifications: {eval_res['correct_matches']} / {eval_res['total_records']}")
    print(f"  Exceptions Detected:           {eval_res['exceptions_detected']}")
    print(f"  False Positives:               {eval_res['false_positives']}")
    print(f"  False Negatives:               {eval_res['false_negatives']}")
    print("-" * 72)
    print(f"  Match Accuracy:                {eval_res['match_accuracy']:.1f}%")
    print(f"  Exception Precision:           {eval_res['exception_precision']:.1f}%")
    print(f"  Exception Recall:              {eval_res['exception_recall']:.1f}%")
    print(f"  F1 Composite Score:            {eval_res['f1_score']:.1f}%")
    print(f"  Execution Time:                {eval_res['execution_time_s']:.4f} s")
    print(f"  Throughput:                    {eval_res['throughput_rps']:,.1f} records/sec")
    print("=" * 72)

    if output_json_path:
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump({
                "benchmark_name": "FinPilot-120-Finance-Controller-Benchmark",
                "timestamp": run_res["timestamp"],
                "run_summary": run_res,
                "evaluation_metrics": eval_res
            }, f, indent=2)
        print(f"\n[PASSED] Machine-readable benchmark report saved to: {output_json_path}")

    passed = (
        eval_res["match_accuracy"] >= 90.0
        and eval_res["exception_precision"] >= 88.0
        and eval_res["exception_recall"] >= 88.0
        and eval_res["f1_score"] >= 88.0
        and eval_res["throughput_rps"] >= 50.0
    )

    if passed:
        print("\n[SUCCESS] BENCHMARK STATUS: PASSED (All correctness thresholds satisfied)")
        return 0
    else:
        print("\n[FAILED] BENCHMARK STATUS: FAILED (Thresholds not met)")
        return 1


if __name__ == "__main__":
    out_file = "benchmark_results.json" if "--json" in sys.argv else None
    exit_code = run_benchmark(output_json_path=out_file)
    sys.exit(exit_code)
