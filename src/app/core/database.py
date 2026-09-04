# -*- coding: utf-8 -*-
"""
FinPilot AI — Enterprise Multi-Engine Database Layer
=====================================================
Provides unified database abstraction supporting:
1. PostgreSQL (Supabase, Render Postgres, Cloud SQL) when DATABASE_URL is set.
2. High-Performance SQLite fallback (finpilot.db) for local / offline execution.
3. Transparent query parameter adaptation (? -> %s).
4. Fast non-blocking connection with 3-second timeout and automatic SQLite fallback.
"""

import os
import json
import re
import time
import sqlite3
import hashlib
import logging
import urllib.parse
from typing import Dict, List, Any, Optional, Tuple

from src.app.core.config import settings

logger = logging.getLogger("DatabaseService")

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "finpilot.db")
BENCHMARK_JSON_PATH = os.path.join(DB_DIR, "finance_benchmark_100.json")

# Try importing psycopg2 for PostgreSQL support
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.warning("[DatabaseService] psycopg2 not installed. Operating in SQLite-only mode.")


def get_sanitized_db_host(db_url: str) -> str:
    """Extracts host and db name without exposing passwords (e.g. db.eymv...supabase.co:5432/postgres)."""
    if not db_url:
        return "SQLite (Local Embedded)"
    try:
        parsed = urllib.parse.urlparse(db_url)
        netloc_safe = parsed.netloc.split("@")[-1] if "@" in parsed.netloc else parsed.netloc
        return f"{netloc_safe}{parsed.path}"
    except Exception:
        return "PostgreSQL (Remote Instance)"


class DBConnectionWrapper:
    """Unified connection and cursor wrapper adapting queries between Postgres and SQLite."""

    def __init__(self, raw_conn, engine_type: str):
        self.raw_conn = raw_conn
        self.engine_type = engine_type  # "POSTGRES" or "SQLITE"

    def cursor(self):
        if self.engine_type == "POSTGRES":
            return PostgresCursorWrapper(self.raw_conn.cursor(cursor_factory=RealDictCursor))
        else:
            return SQLiteCursorWrapper(self.raw_conn.cursor())

    def commit(self):
        self.raw_conn.commit()

    def rollback(self):
        self.raw_conn.rollback()

    def close(self):
        try:
            self.raw_conn.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()


class PostgresCursorWrapper:
    """Adapts ? parameter placeholders and SQLite specific constructs to PostgreSQL."""

    def __init__(self, raw_cursor):
        self.raw_cursor = raw_cursor

    def _adapt_query(self, query: str) -> str:
        adapted = query.replace("?", "%s")
        if "INSERT OR REPLACE INTO" in adapted:
            adapted = adapted.replace("INSERT OR REPLACE INTO", "INSERT INTO")
        # SQLite exposes an implicit ROWID for insertion-order sorting; the
        # PostgreSQL equivalent is the system column CTID. Translate it so
        # ORDER BY rowid ... LIMIT n queries work on both engines.
        if re.search(r"\browid\b", adapted, flags=re.IGNORECASE):
            adapted = re.sub(r"\browid\b", "ctid", adapted)
        return adapted

    def execute(self, query: str, params: Optional[Tuple] = None):
        adapted = self._adapt_query(query)
        if params is not None:
            self.raw_cursor.execute(adapted, params)
        else:
            self.raw_cursor.execute(adapted)
        # Return the wrapper (not the raw result) so chained calls like
        # cursor.execute(...).fetchone() work on both engines.
        return self

    def executemany(self, query: str, seq_of_params):
        adapted = self._adapt_query(query)
        self.raw_cursor.executemany(adapted, seq_of_params)
        return self

    def fetchone(self):
        res = self.raw_cursor.fetchone()
        if res is None:
            return None
        return DictWithTupleAccess(dict(res))

    def fetchall(self):
        rows = self.raw_cursor.fetchall()
        return [DictWithTupleAccess(dict(r)) for r in rows]

    def close(self):
        try:
            self.raw_cursor.close()
        except Exception:
            pass


class SQLiteCursorWrapper:
    """Wrapper around SQLite cursor returning DictWithTupleAccess rows."""

    def __init__(self, raw_cursor):
        self.raw_cursor = raw_cursor

    def execute(self, query: str, params: Optional[Tuple] = None):
        if params is not None:
            self.raw_cursor.execute(query, params)
        else:
            self.raw_cursor.execute(query)
        # Return the wrapper (not the raw result) so chained calls like
        # cursor.execute(...).fetchone() behave identically on both engines.
        return self

    def executemany(self, query: str, seq_of_params):
        self.raw_cursor.executemany(query, seq_of_params)
        return self

    def fetchone(self):
        res = self.raw_cursor.fetchone()
        if res is None:
            return None
        return DictWithTupleAccess(dict(res))

    def fetchall(self):
        rows = self.raw_cursor.fetchall()
        return [DictWithTupleAccess(dict(r)) for r in rows]

    def close(self):
        try:
            self.raw_cursor.close()
        except Exception:
            pass


class DictWithTupleAccess(dict):
    """Allows row access via row['column'] and row[0] (integer indices)."""

    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


def get_db_connection() -> DBConnectionWrapper:
    """
    Returns an active database connection wrapper.
    Connects to PostgreSQL (Supabase / Render) with a fast 3-second timeout,
    falling back instantly to SQLite (finpilot.db) if unreachable.
    """
    db_url = (settings.DATABASE_URL or "").strip()

    if PSYCOPG2_AVAILABLE and db_url and (db_url.startswith("postgresql://") or db_url.startswith("postgres://")):
        try:
            conn = psycopg2.connect(db_url, sslmode="require", connect_timeout=3)
            return DBConnectionWrapper(conn, "POSTGRES")
        except Exception as e:
            logger.warning(f"[DatabaseService] PostgreSQL connection failed ({e}). Falling back to SQLite.")

    # SQLite Fallback (also the default when DATABASE_URL is unset)
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    wrapper = DBConnectionWrapper(conn, "SQLITE")
    if "SQLITE" not in _db_initialized_engines:
        # Ensure schema + seed exist on fallback DBs too (fresh checkout, or
        # Postgres was reachable at startup but is unreachable now), so the
        # app serves seeded demo data instead of empty missing-table errors.
        init_db(existing_conn=wrapper)
        fresh = sqlite3.connect(DB_PATH, timeout=10.0)
        fresh.row_factory = sqlite3.Row
        return DBConnectionWrapper(fresh, "SQLITE")
    return wrapper


_db_initialized_engines = set()

def init_db(existing_conn=None):
    """Initializes database schema and seeds benchmark dataset.

    Idempotent per engine (POSTGRES / SQLITE). Accepts an optional existing
    connection (used by the SQLite fallback path); otherwise opens one.
    """
    global _db_initialized_engines

    owns_conn = existing_conn is None
    conn = existing_conn or get_db_connection()
    if conn.engine_type in _db_initialized_engines:
        if owns_conn:
            conn.close()
        return

    os.makedirs(DB_DIR, exist_ok=True)
    cursor = conn.cursor()

    is_postgres = conn.engine_type == "POSTGRES"

    dtype_double = "DOUBLE PRECISION" if is_postgres else "REAL"
    dtype_autoincrement = "SERIAL PRIMARY KEY" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"

    cursor.execute(f"""
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
        payment_amount {dtype_double} NOT NULL,
        invoice_amount {dtype_double},
        processing_fee {dtype_double},
        fee_gst {dtype_double},
        expected_net_amount {dtype_double},
        actual_settled_amount {dtype_double},
        amount_difference {dtype_double},
        payment_timestamp TEXT,
        settlement_timestamp TEXT,
        settlement_delay_days INTEGER,
        status TEXT,
        ground_truth_exception TEXT,
        ground_truth_reason TEXT
    );
    """)

    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS reconciliation_runs (
        run_id TEXT PRIMARY KEY,
        tenant_id TEXT DEFAULT 'merchant_default',
        timestamp TEXT NOT NULL,
        records_processed INTEGER NOT NULL,
        auto_reconciled INTEGER NOT NULL,
        match_rate {dtype_double} NOT NULL,
        exceptions_count INTEGER NOT NULL,
        auto_resolved INTEGER NOT NULL,
        human_review INTEGER NOT NULL,
        amount_under_review {dtype_double} NOT NULL,
        duration_ms {dtype_double} NOT NULL,
        throughput_rps {dtype_double} NOT NULL,
        status TEXT NOT NULL
    );
    """)

    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS reconciliation_items (
        id {dtype_autoincrement},
        run_id TEXT NOT NULL,
        tenant_id TEXT DEFAULT 'merchant_default',
        record_id TEXT NOT NULL,
        match_status TEXT NOT NULL,
        payment_amount {dtype_double},
        invoice_amount {dtype_double},
        settled_amount {dtype_double},
        variance {dtype_double},
        match_type TEXT,
        confidence {dtype_double},
        details TEXT
    );
    """)

    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS controller_exceptions (
        exception_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        tenant_id TEXT DEFAULT 'merchant_default',
        record_id TEXT NOT NULL,
        transaction_id TEXT,
        invoice_id TEXT,
        exception_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        amount_difference {dtype_double} NOT NULL,
        status TEXT NOT NULL,
        confidence {dtype_double},
        ai_issue TEXT,
        ai_evidence TEXT,
        ai_root_cause TEXT,
        ai_recommendation TEXT,
        policy_triggered TEXT,
        created_at TEXT NOT NULL
    );
    """)

    cursor.execute(f"""
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
        correlation_id TEXT
    );
    """)

    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS controller_audit_events (
        id {dtype_autoincrement},
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

    cursor.execute(f"""
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
        match_accuracy {dtype_double} NOT NULL,
        exception_precision {dtype_double} NOT NULL,
        exception_recall {dtype_double} NOT NULL,
        f1_score {dtype_double} NOT NULL,
        execution_time_s {dtype_double} NOT NULL,
        throughput_rps {dtype_double} NOT NULL,
        timestamp TEXT NOT NULL
    );
    """)

    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_recon_items_run ON reconciliation_items(run_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_exceptions_run_status ON controller_exceptions(run_id, status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_entity ON controller_audit_events(entity_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_benchmark_txn ON benchmark_records(transaction_id, invoice_id);")
    except Exception:
        pass

    cursor.execute("SELECT COUNT(*) FROM benchmark_records;")
    count = cursor.fetchone()[0]

    if count == 0 and os.path.exists(BENCHMARK_JSON_PATH):
        try:
            with open(BENCHMARK_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                records = data.get("benchmark_records", []) if isinstance(data, dict) else data

            insert_sql = """
            INSERT INTO benchmark_records (
                record_id, tenant_id, transaction_id, invoice_id, settlement_id, utr,
                customer_name, customer_id, customer_email, vendor_name,
                payment_amount, invoice_amount, processing_fee, fee_gst,
                expected_net_amount, actual_settled_amount, amount_difference,
                payment_timestamp, settlement_timestamp, settlement_delay_days,
                status, ground_truth_exception, ground_truth_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            if is_postgres:
                insert_sql += " ON CONFLICT (record_id) DO NOTHING;"

            for r in records:
                cursor.execute(insert_sql, (
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
            logger.info(f"[DatabaseService] Successfully seeded {len(records)} benchmark records.")
        except Exception as e:
            logger.error(f"[DatabaseService] Error seeding benchmark records: {e}")

    conn.commit()
    conn.close()
    _db_initialized_engines.add(conn.engine_type)


def get_database_status() -> Dict[str, Any]:
    """Returns real-time database connection metrics, engine name, host, and table counts."""
    t0 = time.perf_counter()
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM benchmark_records;")
        bench_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM reconciliation_runs;")
        runs_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM controller_exceptions;")
        exc_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM controller_audit_events;")
        audit_count = cur.fetchone()[0]
        conn.close()
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)

        engine_name = "PostgreSQL (Supabase / Remote)" if conn.engine_type == "POSTGRES" else "SQLite (Local File)"
        return {
            "connected": True,
            "engine": engine_name,
            "raw_engine": conn.engine_type,
            "host": get_sanitized_db_host(settings.DATABASE_URL) if conn.engine_type == "POSTGRES" else "finpilot.db",
            "latency_ms": latency_ms,
            "sslmode": "require" if conn.engine_type == "POSTGRES" else "N/A",
            "tables": {
                "benchmark_records": bench_count,
                "reconciliation_runs": runs_count,
                "controller_exceptions": exc_count,
                "controller_audit_events": audit_count
            }
        }
    except Exception as e:
        return {
            "connected": False,
            "engine": "Unknown",
            "error": str(e),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2)
        }


def get_db_stats() -> Dict[str, Any]:
    stat = get_database_status()
    return {
        "connected": stat.get("connected", False),
        "engine": "Postgres" if stat.get("raw_engine") == "POSTGRES" else "SQLite",
        "benchmark_records_seeded": stat.get("tables", {}).get("benchmark_records", 120),
        "reconciliation_runs_executed": stat.get("tables", {}).get("reconciliation_runs", 0),
        "host": stat.get("host", "N/A")
    }


def generate_sha256_audit_hash(event_data: Dict[str, Any], prev_hash: str) -> str:
    canonical_payload = json.dumps(event_data, sort_keys=True)
    chain_input = f"{canonical_payload}|{prev_hash}".encode("utf-8")
    return hashlib.sha256(chain_input).hexdigest()
