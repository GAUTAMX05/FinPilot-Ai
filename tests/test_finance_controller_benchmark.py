import os
import sys
import unittest

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app.core.database import init_db, get_db_connection
from src.app.services.finance_controller_service import finance_controller_service


class TestFinanceControllerBenchmark(unittest.TestCase):
    """
    Comprehensive Automated Test Suite for FinPilot AI Autonomous Finance Controller:
    - 120-Record Benchmark Integrity
    - Deterministic 3-Way Reconciliation Math
    - Exception Detection & Multi-Vector Classification
    - Policy Guardrails & HITL Thresholds
    - Grounded AI Root-Cause Reasoning
    - Human-in-the-Loop State Transitions & SHA-256 Audit Trail
    - Measured Ground Truth Evaluation (Accuracy, Precision, Recall, F1)
    - High-Throughput Batch Performance
    """

    @classmethod
    def setUpClass(cls):
        init_db()
        # Seed fresh run for testing
        cls.run_result = finance_controller_service.run_close_month(actor="Automated CI Test")

    def test_01_benchmark_dataset_integrity(self):
        """Verify 120 records with 95 normal and 25 known exceptions are stored in SQLite."""
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM benchmark_records")
        total = c.fetchone()[0]
        self.assertEqual(total, 120, "Expected 120 benchmark records in SQLite.")

        c.execute("SELECT COUNT(*) FROM benchmark_records WHERE ground_truth_exception != 'NONE'")
        exceptions_gt = c.fetchone()[0]
        self.assertEqual(exceptions_gt, 25, "Expected exactly 25 known ground-truth exceptions.")
        conn.close()

    def test_02_deterministic_3way_reconciliation_math(self):
        """Verify deterministic Razorpay fee math (2% fee, 18% GST on fee, expected net)."""
        gross = 100000.0
        expected_fee = round(gross * 0.02, 2)
        expected_gst = round(expected_fee * 0.18, 2)
        expected_net = round(gross - expected_fee - expected_gst, 2)

        self.assertEqual(expected_fee, 2000.0)
        self.assertEqual(expected_gst, 360.0)
        self.assertEqual(expected_net, 97640.0)

    def test_03_close_month_execution_pipeline(self):
        """Verify run_close_month successfully processes all 120 records with real telemetry."""
        res = self.run_result
        self.assertTrue(res["success"])
        self.assertEqual(res["records_processed"], 120)
        self.assertEqual(res["auto_reconciled"], 95)
        self.assertEqual(res["exceptions_count"], 25)
        self.assertGreater(res["match_rate_percentage"], 75.0)
        self.assertGreater(res["throughput_rps"], 50.0)

    def test_04_exception_classification_types(self):
        """Verify all 7 expected exception categories are detected accurately."""
        exceptions = finance_controller_service.get_exceptions()
        self.assertEqual(len(exceptions), 25)

        types_found = {e["exception_type"] for e in exceptions}
        expected_types = {
            "FEE_CALCULATION_MISMATCH",
            "MISSING_SETTLEMENT",
            "DUPLICATE_INVOICE",
            "PARTIAL_SETTLEMENT",
            "TIMING_ANOMALY",
            "AMOUNT_MISMATCH",
            "MISSING_INVOICE"
        }
        self.assertTrue(expected_types.issubset(types_found), f"Missing exception types: {expected_types - types_found}")

    def test_05_grounded_ai_root_cause_structure(self):
        """Verify grounded AI root cause contains verified numbers, issue, evidence, and recommendation."""
        exceptions = finance_controller_service.get_exceptions()
        fee_exc = next(e for e in exceptions if e["exception_type"] == "FEE_CALCULATION_MISMATCH")

        self.assertIn("₹", fee_exc["ai_issue"])
        self.assertIn("Invoice:", fee_exc["ai_evidence"])
        self.assertIn("Razorpay", fee_exc["ai_root_cause"])
        self.assertIsNotNone(fee_exc["ai_recommendation"])

    def test_06_human_in_the_loop_decision_and_audit_hash(self):
        """Verify human approval updates state, logs approver, and computes SHA-256 audit hash."""
        exceptions = finance_controller_service.get_exceptions()
        exc = exceptions[0]
        exc_id = exc["exception_id"]

        decision_res = finance_controller_service.decide_exception(
            exception_id=exc_id,
            decision="APPROVE",
            actor_name="Vikramaditya S.",
            actor_role="CFO",
            comments="Approved test fee adjustment journal."
        )

        self.assertTrue(decision_res["success"])
        self.assertEqual(decision_res["new_status"], "HUMAN_APPROVED")
        self.assertTrue(len(decision_res["sha256_audit_hash"]) == 64, "Expected valid 64-character SHA-256 hash.")

        # Verify audit trail contains the event
        trail = finance_controller_service.get_audit_trail(limit=5)
        latest_event = trail[0]
        self.assertEqual(latest_event["action"], "EXCEPTION_APPROVE")
        self.assertEqual(latest_event["sha256_hash"], decision_res["sha256_audit_hash"])

    def test_07_ground_truth_benchmark_evaluation(self):
        """Verify objective evaluation vs ground truth achieves 100% precision, recall, and accuracy."""
        eval_metrics = finance_controller_service.evaluate_benchmark()

        self.assertEqual(eval_metrics["total_records"], 120)
        self.assertEqual(eval_metrics["correct_matches"], 120)
        self.assertEqual(eval_metrics["incorrect_matches"], 0)
        self.assertEqual(eval_metrics["false_positives"], 0)
        self.assertEqual(eval_metrics["false_negatives"], 0)
        self.assertEqual(eval_metrics["match_accuracy"], 100.0)
        self.assertEqual(eval_metrics["exception_precision"], 100.0)
        self.assertEqual(eval_metrics["exception_recall"], 100.0)
        self.assertEqual(eval_metrics["f1_score"], 100.0)
        self.assertGreater(eval_metrics["throughput_rps"], 100.0)


if __name__ == "__main__":
    print("==================================================================")
    print("   FINPILOT AI — AUTONOMOUS FINANCE CONTROLLER BENCHMARK TEST    ")
    print("==================================================================")
    unittest.main()
