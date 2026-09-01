import os
import json
import sqlite3
import hashlib
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger("DatabaseService")

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "finpilot.db")
BENCHMARK_JSON_PATH = os.path.join(DB_DIR, "finance_benchmark_100.json")


def get_db_connection() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes SQLite schema and populates default benchmark data if empty."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Benchmark Financial Records Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS benchmark_records (
        record_id TEXT PRIMARY KEY,
        transaction_id TEXT NOT NULL,
        invoice_id TEXT,
        settlement_id TEXT,
        utr TEXT,
        customer_name TEXT,
        customer_id TEXT,
        customer_email TEXT,
        vendor_name TEXT,
        payment_amount REAL NOT NULL,
        invoice_amount REAL,
        processing_fee REAL,
        fee_gst REAL,
        expected_net_amount REAL,
        actual_settled_amount REAL,
        amount_difference REAL,
        payment_timestamp TEXT,
        settlement_timestamp TEXT,
        settlement_delay_days INTEGER,
        status TEXT,
        ground_truth_exception TEXT,
        ground_truth_reason TEXT
    );
    """)

    # 2. Reconciliation Runs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reconciliation_runs (
        run_id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        records_processed INTEGER NOT NULL,
        auto_reconciled INTEGER NOT NULL,
        match_rate REAL NOT NULL,
        exceptions_count INTEGER NOT NULL,
        auto_resolved INTEGER NOT NULL,
        human_review INTEGER NOT NULL,
        amount_under_review REAL NOT NULL,
        duration_ms REAL NOT NULL,
        throughput_rps REAL NOT NULL,
        status TEXT NOT NULL
    );
    """)

    # 3. Reconciliation Items
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reconciliation_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        record_id TEXT NOT NULL,
        match_status TEXT NOT NULL,
        payment_amount REAL,
        invoice_amount REAL,
        settled_amount REAL,
        variance REAL,
        match_type TEXT,
        confidence REAL,
        details TEXT,
        FOREIGN KEY(run_id) REFERENCES reconciliation_runs(run_id)
    );
    """)

    # 4. Exceptions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS controller_exceptions (
        exception_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        record_id TEXT NOT NULL,
        transaction_id TEXT,
        invoice_id TEXT,
        exception_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        amount_difference REAL NOT NULL,
        status TEXT NOT NULL,
        confidence REAL,
        ai_issue TEXT,
        ai_evidence TEXT,
        ai_root_cause TEXT,
        ai_recommendation TEXT,
        policy_triggered TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # 5. Human-in-the-Loop Approvals
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS controller_approvals (
        approval_id TEXT PRIMARY KEY,
        exception_id TEXT NOT NULL,
        decision TEXT NOT NULL,
        actor_name TEXT NOT NULL,
        actor_role TEXT NOT NULL,
        comments TEXT,
        timestamp TEXT NOT NULL,
        previous_status TEXT,
        new_status TEXT
    );
    """)

    # 6. Immutable Chained Audit Events
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS controller_audit_events (
        event_id TEXT PRIMARY KEY,
        decision_id TEXT,
        actor TEXT NOT NULL,
        action TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        entity TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        reason TEXT,
        previous_state TEXT,
        new_state TEXT,
        sha256_hash TEXT NOT NULL,
        prev_hash TEXT
    );
    """)

    # 7. Evaluation Metrics
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evaluation_metrics (
        run_id TEXT PRIMARY KEY,
        total_records INTEGER NOT NULL,
        correct_matches INTEGER NOT NULL,
        incorrect_matches INTEGER NOT NULL,
        exceptions_detected INTEGER NOT NULL,
        exceptions_missed INTEGER NOT NULL,
        false_positives INTEGER NOT NULL,
        false_negatives INTEGER NOT NULL,
        match_accuracy REAL NOT NULL,
        exception_precision REAL NOT NULL,
        exception_recall REAL NOT NULL,
        f1_score REAL NOT NULL,
        execution_time_s REAL NOT NULL,
        throughput_rps REAL NOT NULL,
        timestamp TEXT NOT NULL
    );
    """)

    conn.commit()

    # Seed benchmark records if empty
    cursor.execute("SELECT COUNT(*) FROM benchmark_records")
    count = cursor.fetchone()[0]
    if count == 0 and os.path.exists(BENCHMARK_JSON_PATH):
        try:
            with open(BENCHMARK_JSON_PATH, "r", encoding="utf-8") as f:
                records = json.load(f)
            for r in records:
                cursor.execute("""
                INSERT INTO benchmark_records (
                    record_id, transaction_id, invoice_id, settlement_id, utr,
                    customer_name, customer_id, customer_email, vendor_name,
                    payment_amount, invoice_amount, processing_fee, fee_gst,
                    expected_net_amount, actual_settled_amount, amount_difference,
                    payment_timestamp, settlement_timestamp, settlement_delay_days,
                    status, ground_truth_exception, ground_truth_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    r.get("record_id"), r.get("transaction_id"), r.get("invoice_id"), r.get("settlement_id"), r.get("utr"),
                    r.get("customer_name"), r.get("customer_id"), r.get("customer_email"), r.get("vendor_name"),
                    r.get("payment_amount", 0.0), r.get("invoice_amount", 0.0), r.get("processing_fee", 0.0), r.get("fee_gst", 0.0),
                    r.get("expected_net_amount", 0.0), r.get("actual_settled_amount", 0.0), r.get("amount_difference", 0.0),
                    r.get("payment_timestamp"), r.get("settlement_timestamp"), r.get("settlement_delay_days", 2),
                    r.get("status"), r.get("ground_truth_exception", "NONE"), r.get("ground_truth_reason", "")
                ))
            conn.commit()
            logger.info(f"Seeded {len(records)} benchmark records into SQLite database.")
        except Exception as e:
            logger.error(f"Failed to seed benchmark records: {e}")

    conn.close()


def generate_sha256_audit_hash(event_data: Dict[str, Any], prev_hash: Optional[str] = None) -> str:
    """Computes a SHA-256 hash chained to the previous audit log entry."""
    payload = f"{event_data.get('event_id')}|{event_data.get('timestamp')}|{event_data.get('actor')}|{event_data.get('action')}|{event_data.get('entity_id')}|{prev_hash or 'GENESIS_HASH'}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
