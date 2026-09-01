# -*- coding: utf-8 -*-
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
    """Returns an active SQLite database connection with row factory enabled."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Initializes SQLite schema with tenant awareness, correlation IDs, and indexes.
    Populates default 120-record benchmark dataset if database is empty.
    """
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Benchmark Financial Records Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS benchmark_records (
        record_id TEXT PRIMARY KEY,
        tenant_id TEXT DEFAULT 'merchant_default',
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

    # 2. Reconciliation Runs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reconciliation_runs (
        run_id TEXT PRIMARY KEY,
        tenant_id TEXT DEFAULT 'merchant_default',
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

    # 3. Reconciliation Items Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reconciliation_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        tenant_id TEXT DEFAULT 'merchant_default',
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

    # 4. Controller Exceptions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS controller_exceptions (
        exception_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        tenant_id TEXT DEFAULT 'merchant_default',
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

    # 5. Human-in-the-Loop Approvals Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS controller_approvals (
        approval_id TEXT PRIMARY KEY,
        tenant_id TEXT DEFAULT 'merchant_default',
        exception_id TEXT NOT NULL,
        decision TEXT NOT NULL,
        actor_name TEXT NOT NULL,
        actor_role TEXT NOT NULL,
        comments TEXT,
        timestamp TEXT NOT NULL,
        previous_status TEXT,
        new_status TEXT,
        request_id TEXT,
        correlation_id TEXT,
        FOREIGN KEY(exception_id) REFERENCES controller_exceptions(exception_id)
    );
    """)

    # 6. Cryptographic Chained Audit Events Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS controller_audit_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT DEFAULT 'merchant_default',
        event_id TEXT NOT NULL,
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
        prev_hash TEXT NOT NULL,
        request_id TEXT,
        correlation_id TEXT
    );
    """)

    # 7. Measured Evaluation Metrics Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evaluation_metrics (
        run_id TEXT PRIMARY KEY,
        tenant_id TEXT DEFAULT 'merchant_default',
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

    # 8. Indexes for High Performance Querying
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_recon_items_run ON reconciliation_items(run_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exceptions_run_status ON controller_exceptions(run_id, status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_entity ON controller_audit_events(entity_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_benchmark_txn ON benchmark_records(transaction_id, invoice_id);")

    # Safe Schema Migrations (Add tenant_id / correlation_id if missing from earlier tables)
    def _add_col_if_missing(table, col, col_def):
        cursor.execute(f"PRAGMA table_info({table})")
        cols = [r[1] for r in cursor.fetchall()]
        if col not in cols:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")
            except Exception as e:
                logger.debug(f"Migration note: {e}")

    _add_col_if_missing("benchmark_records", "tenant_id", "TEXT DEFAULT 'merchant_default'")
    _add_col_if_missing("reconciliation_runs", "tenant_id", "TEXT DEFAULT 'merchant_default'")
    _add_col_if_missing("reconciliation_items", "tenant_id", "TEXT DEFAULT 'merchant_default'")
    _add_col_if_missing("controller_exceptions", "tenant_id", "TEXT DEFAULT 'merchant_default'")
    _add_col_if_missing("controller_approvals", "tenant_id", "TEXT DEFAULT 'merchant_default'")
    _add_col_if_missing("controller_approvals", "request_id", "TEXT")
    _add_col_if_missing("controller_approvals", "correlation_id", "TEXT")
    _add_col_if_missing("controller_audit_events", "tenant_id", "TEXT DEFAULT 'merchant_default'")
    _add_col_if_missing("controller_audit_events", "request_id", "TEXT")
    _add_col_if_missing("controller_audit_events", "correlation_id", "TEXT")
    _add_col_if_missing("evaluation_metrics", "tenant_id", "TEXT DEFAULT 'merchant_default'")

    # Seed Benchmark Dataset if benchmark_records table is empty
    cursor.execute("SELECT COUNT(*) FROM benchmark_records")
    count = cursor.fetchone()[0]

    if count == 0 and os.path.exists(BENCHMARK_JSON_PATH):
        try:
            with open(BENCHMARK_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                records = data.get("benchmark_records", [])

            for r in records:
                cursor.execute("""
                INSERT OR REPLACE INTO benchmark_records (
                    record_id, tenant_id, transaction_id, invoice_id, settlement_id, utr,
                    customer_name, customer_id, customer_email, vendor_name,
                    payment_amount, invoice_amount, processing_fee, fee_gst,
                    expected_net_amount, actual_settled_amount, amount_difference,
                    payment_timestamp, settlement_timestamp, settlement_delay_days,
                    status, ground_truth_exception, ground_truth_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    r.get("record_id"), r.get("tenant_id", "merchant_default"), r.get("transaction_id"), r.get("invoice_id"),
                    r.get("settlement_id"), r.get("utr"), r.get("customer_name"),
                    r.get("customer_id"), r.get("customer_email"), r.get("vendor_name"),
                    r.get("payment_amount", 0.0), r.get("invoice_amount", 0.0),
                    r.get("processing_fee", 0.0), r.get("fee_gst", 0.0),
                    r.get("expected_net_amount", 0.0), r.get("actual_settled_amount", 0.0),
                    r.get("amount_difference", 0.0), r.get("payment_timestamp"),
                    r.get("settlement_timestamp"), r.get("settlement_delay_days", 2),
                    r.get("status", "NORMAL"), r.get("ground_truth_exception", "NONE"),
                    r.get("ground_truth_reason")
                ))
            logger.info(f"[DatabaseService] Successfully seeded {len(records)} benchmark records into SQLite.")
        except Exception as e:
            logger.error(f"[DatabaseService] Error seeding benchmark records: {e}")

    conn.commit()
    conn.close()


def generate_sha256_audit_hash(event_data: Dict[str, Any], prev_hash: str) -> str:
    """Generates an immutable cryptographic SHA-256 hash chaining event payload with the previous hash."""
    canonical_payload = json.dumps(event_data, sort_keys=True)
    chain_input = f"{canonical_payload}|{prev_hash}".encode("utf-8")
    return hashlib.sha256(chain_input).hexdigest()
