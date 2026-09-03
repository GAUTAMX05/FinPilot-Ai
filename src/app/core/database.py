# -*- coding: utf-8 -*-
"""
FinPilot AI — Database layer (SQLite local + Postgres Supabase/Neon ready)
===========================================================================
- Default: SQLite file at src/app/data/finpilot.db (zero-setup, tests, local).
- Production: any Postgres DATABASE_URL (Supabase, Neon, Render Postgres).
  Set DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
  The same get_db_connection() API works for both engines.

Postgres compatibility strategy (minimal, non-breaking):
  - Placeholder translation: SQLite '?' -> Postgres '%s' (auto in wrapper).
  - 'rowid' -> 'ctid' translation (Postgres physical row id, same insertion-order semantics).
  - CompatRow(dict): supports both dict access row['col'] AND index access row[0]
    so existing `fetchone()[0]` + `dict(row)` code works unchanged.
  - DDL branches: SQLite AUTOINCREMENT/PRAGMA vs Postgres SERIAL/information_schema.
  - Seed uses INSERT ... ON CONFLICT DO NOTHING on Postgres, OR REPLACE on SQLite.
  - SSL auto-added for *.supabase.co / *.neon.tech when no sslmode present.

No secrets are logged. DATABASE_URL is never printed.
"""
import os
import json
import sqlite3
import hashlib
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

logger = logging.getLogger("DatabaseService")

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "finpilot.db")
BENCHMARK_JSON_PATH = os.path.join(DB_DIR, "finance_benchmark_100.json")


# ---------------------------------------------------------------------------
# Engine detection
# ---------------------------------------------------------------------------

def _get_database_url() -> str:
    return (os.getenv("DATABASE_URL", "") or "").strip().strip('"').strip("'")


def get_database_engine() -> str:
    """'postgres' when DATABASE_URL is postgres-like, else 'sqlite'."""
    url = _get_database_url().lower()
    if url.startswith("postgres://") or url.startswith("postgresql://"):
        return "postgres"
    return "sqlite"


def is_postgres() -> bool:
    return get_database_engine() == "postgres"


def _ensure_sslmode(url: str) -> str:
    """Add sslmode=require for Supabase/Neon when missing (psycopg2)."""
    try:
        low = url.lower()
        if ("supabase.co" in low or "neon.tech" in low) and "sslmode" not in low:
            parts = urlparse(url)
            q = dict(parse_qsl(parts.query))
            q.setdefault("sslmode", "require")
            return urlunparse(parts._replace(query=urlencode(q)))
    except Exception:
        pass
    return url


# ---------------------------------------------------------------------------
# Postgres compatibility wrapper (translates SQLite dialect -> Postgres)
# ---------------------------------------------------------------------------

class CompatRow(dict):
    """dict subclass supporting integer index access (row[0]) like sqlite3.Row."""

    def __getitem__(self, key):
        if isinstance(key, int):
            try:
                return list(self.values())[key]
            except IndexError:
                raise KeyError(key)
        return super().__getitem__(key)


def _translate_sql(sql: str) -> str:
    """Translate SQLite-isms to Postgres. No-op for SQLite paths."""
    if "rowid" in sql:
        # ctid is Postgres' closest equivalent for insertion-order sorting
        sql = sql.replace("rowid", "ctid")
    # '?' placeholders -> '%s' (only when not already containing '%s')
    if "?" in sql and "%s" not in sql:
        sql = sql.replace("?", "%s")
    return sql


class _PgCursorWrapper:
    def __init__(self, cur):
        self._cur = cur
        # RealDictCursor description gives column names in order
        self._cols: List[str] = []

    def _wrap_row(self, row) -> Optional[CompatRow]:
        if row is None:
            return None
        if isinstance(row, dict):
            return CompatRow(row)
        # tuple + description fallback
        try:
            cols = [d[0] for d in (self._cur.description or [])]
            if cols and len(cols) == len(row):
                return CompatRow(zip(cols, row))
        except Exception:
            pass
        # last resort: numeric keys
        return CompatRow({i: v for i, v in enumerate(row)})

    def execute(self, sql, params=None):
        sql = _translate_sql(sql)
        if params is None:
            self._cur.execute(sql)
        else:
            self._cur.execute(sql, params)
        return self

    def executemany(self, sql, seq):
        return self._cur.executemany(_translate_sql(sql), seq)

    def fetchone(self):
        return self._wrap_row(self._cur.fetchone())

    def fetchall(self):
        return [self._wrap_row(r) for r in self._cur.fetchall()]

    def __getattr__(self, name):
        return getattr(self._cur, name)


class _PgConnectionWrapper:
    """Wraps psycopg2 connection to look like sqlite3 (cursor/commit/close/context)."""

    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        from psycopg2.extras import RealDictCursor
        return _PgCursorWrapper(self._conn.cursor(cursor_factory=RealDictCursor))

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        try:
            self._conn.commit()
        finally:
            self._conn.close()
        return False

    def __getattr__(self, name):
        return getattr(self._conn, name)


def get_db_connection():
    """Returns a DB connection for the configured engine.

    SQLite: sqlite3.Connection with Row factory (existing behaviour).
    Postgres: psycopg2 connection wrapped for '?'->'%s', rowid->ctid,
      dict+index row access. Caller code stays unchanged.
    """
    if is_postgres():
        try:
            import psycopg2
            import psycopg2.extras
        except ImportError as e:
            raise RuntimeError(
                "DATABASE_URL is Postgres but psycopg2-binary is not installed. "
                "Run: pip install psycopg2-binary"
            ) from e
        url = _ensure_sslmode(_get_database_url())
        conn = psycopg2.connect(url, connect_timeout=10)
        conn.autocommit = False
        return _PgConnectionWrapper(conn)
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    return conn


def get_db_stats(safe: bool = True) -> Dict[str, Any]:
    """Engine + table counts for /ready without leaking credentials."""
    engine = get_database_engine()
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM benchmark_records")
        bench = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM reconciliation_runs")
        runs = c.fetchone()[0]
        conn.close()
        return {"engine": "Postgres" if engine == "postgres" else "SQLite",
                "connected": True, "benchmark_records_seeded": bench,
                "reconciliation_runs_executed": runs}
    except Exception as e:
        logger.error(f"[DatabaseService] stats failed: {e}")
        if safe:
            return {"engine": "Postgres" if engine == "postgres" else "SQLite",
                    "connected": False, "error": str(e)[:200]}
        raise


# ---------------------------------------------------------------------------
# Schema (branched DDL)
# ---------------------------------------------------------------------------

_SQLITE_SCHEMA = [
    """CREATE TABLE IF NOT EXISTS benchmark_records (
        record_id TEXT PRIMARY KEY, tenant_id TEXT DEFAULT 'merchant_default',
        transaction_id TEXT NOT NULL, invoice_id TEXT, settlement_id TEXT, utr TEXT,
        customer_name TEXT, customer_id TEXT, customer_email TEXT, vendor_name TEXT,
        payment_amount REAL NOT NULL, invoice_amount REAL, processing_fee REAL, fee_gst REAL,
        expected_net_amount REAL, actual_settled_amount REAL, amount_difference REAL,
        payment_timestamp TEXT, settlement_timestamp TEXT, settlement_delay_days INTEGER,
        status TEXT, ground_truth_exception TEXT, ground_truth_reason TEXT
    );""",
    """CREATE TABLE IF NOT EXISTS reconciliation_runs (
        run_id TEXT PRIMARY KEY, tenant_id TEXT DEFAULT 'merchant_default',
        timestamp TEXT NOT NULL, records_processed INTEGER NOT NULL,
        auto_reconciled INTEGER NOT NULL, match_rate REAL NOT NULL,
        exceptions_count INTEGER NOT NULL, auto_resolved INTEGER NOT NULL,
        human_review INTEGER NOT NULL, amount_under_review REAL NOT NULL,
        duration_ms REAL NOT NULL, throughput_rps REAL NOT NULL, status TEXT NOT NULL
    );""",
    """CREATE TABLE IF NOT EXISTS reconciliation_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL,
        tenant_id TEXT DEFAULT 'merchant_default', record_id TEXT NOT NULL,
        match_status TEXT NOT NULL, payment_amount REAL, invoice_amount REAL,
        settled_amount REAL, variance REAL, match_type TEXT, confidence REAL, details TEXT,
        FOREIGN KEY(run_id) REFERENCES reconciliation_runs(run_id)
    );""",
    """CREATE TABLE IF NOT EXISTS controller_exceptions (
        exception_id TEXT PRIMARY KEY, run_id TEXT NOT NULL,
        tenant_id TEXT DEFAULT 'merchant_default', record_id TEXT NOT NULL,
        transaction_id TEXT, invoice_id TEXT, exception_type TEXT NOT NULL,
        severity TEXT NOT NULL, amount_difference REAL NOT NULL, status TEXT NOT NULL,
        confidence REAL, ai_issue TEXT, ai_evidence TEXT, ai_root_cause TEXT,
        ai_recommendation TEXT, policy_triggered TEXT, created_at TEXT NOT NULL
    );""",
    """CREATE TABLE IF NOT EXISTS controller_approvals (
        approval_id TEXT PRIMARY KEY, tenant_id TEXT DEFAULT 'merchant_default',
        exception_id TEXT NOT NULL, decision TEXT NOT NULL, actor_name TEXT NOT NULL,
        actor_role TEXT NOT NULL, comments TEXT, timestamp TEXT NOT NULL,
        previous_status TEXT, new_status TEXT, request_id TEXT, correlation_id TEXT,
        FOREIGN KEY(exception_id) REFERENCES controller_exceptions(exception_id)
    );""",
    """CREATE TABLE IF NOT EXISTS controller_audit_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id TEXT DEFAULT 'merchant_default',
        event_id TEXT NOT NULL, decision_id TEXT, actor TEXT NOT NULL, action TEXT NOT NULL,
        timestamp TEXT NOT NULL, entity TEXT NOT NULL, entity_id TEXT NOT NULL, reason TEXT,
        previous_state TEXT, new_state TEXT, sha256_hash TEXT NOT NULL, prev_hash TEXT NOT NULL,
        request_id TEXT, correlation_id TEXT
    );""",
    """CREATE TABLE IF NOT EXISTS evaluation_metrics (
        run_id TEXT PRIMARY KEY, tenant_id TEXT DEFAULT 'merchant_default',
        total_records INTEGER NOT NULL, correct_matches INTEGER NOT NULL,
        incorrect_matches INTEGER NOT NULL, exceptions_detected INTEGER NOT NULL,
        exceptions_missed INTEGER NOT NULL, false_positives INTEGER NOT NULL,
        false_negatives INTEGER NOT NULL, match_accuracy REAL NOT NULL,
        exception_precision REAL NOT NULL, exception_recall REAL NOT NULL,
        f1_score REAL NOT NULL, execution_time_s REAL NOT NULL,
        throughput_rps REAL NOT NULL, timestamp TEXT NOT NULL
    );""",
]

# Postgres: same logical schema, SERIAL for auto ids, DOUBLE PRECISION for REAL.
_POSTGRES_SCHEMA = [
    s.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY").replace(" REAL", " DOUBLE PRECISION")
    for s in _SQLITE_SCHEMA
]

_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_recon_items_run ON reconciliation_items(run_id);",
    "CREATE INDEX IF NOT EXISTS idx_exceptions_run_status ON controller_exceptions(run_id, status);",
    "CREATE INDEX IF NOT EXISTS idx_audit_entity ON controller_audit_events(entity_id);",
    "CREATE INDEX IF NOT EXISTS idx_benchmark_txn ON benchmark_records(transaction_id, invoice_id);",
    "CREATE INDEX IF NOT EXISTS idx_tenant_benchmark ON benchmark_records(tenant_id);",
    "CREATE INDEX IF NOT EXISTS idx_tenant_exceptions ON controller_exceptions(tenant_id);",
    "CREATE INDEX IF NOT EXISTS idx_tenant_audit ON controller_audit_events(tenant_id);",
]


def _ensure_migrations_sqlite(cursor):
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


def _ensure_migrations_postgres(cursor):
    # ADD COLUMN IF NOT EXISTS is idempotent on Postgres
    stmts = [
        "ALTER TABLE benchmark_records ADD COLUMN IF NOT EXISTS tenant_id TEXT DEFAULT 'merchant_default';",
        "ALTER TABLE reconciliation_runs ADD COLUMN IF NOT EXISTS tenant_id TEXT DEFAULT 'merchant_default';",
        "ALTER TABLE reconciliation_items ADD COLUMN IF NOT EXISTS tenant_id TEXT DEFAULT 'merchant_default';",
        "ALTER TABLE controller_exceptions ADD COLUMN IF NOT EXISTS tenant_id TEXT DEFAULT 'merchant_default';",
        "ALTER TABLE controller_approvals ADD COLUMN IF NOT EXISTS tenant_id TEXT DEFAULT 'merchant_default';",
        "ALTER TABLE controller_approvals ADD COLUMN IF NOT EXISTS request_id TEXT;",
        "ALTER TABLE controller_approvals ADD COLUMN IF NOT EXISTS correlation_id TEXT;",
        "ALTER TABLE controller_audit_events ADD COLUMN IF NOT EXISTS tenant_id TEXT DEFAULT 'merchant_default';",
        "ALTER TABLE controller_audit_events ADD COLUMN IF NOT EXISTS request_id TEXT;",
        "ALTER TABLE controller_audit_events ADD COLUMN IF NOT EXISTS correlation_id TEXT;",
        "ALTER TABLE evaluation_metrics ADD COLUMN IF NOT EXISTS tenant_id TEXT DEFAULT 'merchant_default';",
    ]
    for s in stmts:
        try:
            cursor.execute(s)
        except Exception as e:
            logger.debug(f"PG migration note: {e}")


def _load_seed_records() -> List[Dict[str, Any]]:
    if not os.path.exists(BENCHMARK_JSON_PATH):
        return []
    with open(BENCHMARK_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get("benchmark_records", [])
    if isinstance(data, list):
        return data
    return []


def init_db():
    """
    Initializes schema with tenant awareness, correlation IDs, and indexes.
    Populates default benchmark dataset if empty. Works on SQLite + Postgres.
    """
    engine = get_database_engine()
    if engine == "sqlite":
        os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    for ddl in (_POSTGRES_SCHEMA if engine == "postgres" else _SQLITE_SCHEMA):
        cursor.execute(ddl)
    for idx in _INDEXES:
        try:
            cursor.execute(idx)
        except Exception as e:
            logger.debug(f"Index note: {e}")

    if engine == "postgres":
        _ensure_migrations_postgres(cursor)
    else:
        _ensure_migrations_sqlite(cursor)

    # Seed if empty
    cursor.execute("SELECT COUNT(*) FROM benchmark_records")
    count = cursor.fetchone()[0]
    if count == 0:
        records = _load_seed_records()
        if records:
            try:
                cols = ("record_id, tenant_id, transaction_id, invoice_id, settlement_id, utr,"
                        " customer_name, customer_id, customer_email, vendor_name,"
                        " payment_amount, invoice_amount, processing_fee, fee_gst,"
                        " expected_net_amount, actual_settled_amount, amount_difference,"
                        " payment_timestamp, settlement_timestamp, settlement_delay_days,"
                        " status, ground_truth_exception, ground_truth_reason")
                for r in records:
                    vals = (r.get("record_id"), r.get("tenant_id", "merchant_default"), r.get("transaction_id"),
                            r.get("invoice_id"), r.get("settlement_id"), r.get("utr"), r.get("customer_name"),
                            r.get("customer_id"), r.get("customer_email"), r.get("vendor_name"),
                            r.get("payment_amount", 0.0), r.get("invoice_amount", 0.0),
                            r.get("processing_fee", 0.0), r.get("fee_gst", 0.0),
                            r.get("expected_net_amount", 0.0), r.get("actual_settled_amount", 0.0),
                            r.get("amount_difference", 0.0), r.get("payment_timestamp"),
                            r.get("settlement_timestamp"), r.get("settlement_delay_days", 2),
                            r.get("status", "NORMAL"), r.get("ground_truth_exception", "NONE"),
                            r.get("ground_truth_reason"))
                    if engine == "postgres":
                        cursor.execute(
                            f"INSERT INTO benchmark_records ({cols}) VALUES "
                            "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                            "ON CONFLICT (record_id) DO NOTHING", vals)
                    else:
                        cursor.execute(
                            f"INSERT OR REPLACE INTO benchmark_records ({cols}) VALUES "
                            "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", vals)
                logger.info(f"[DatabaseService] Seeded {len(records)} benchmark records ({engine}).")
            except Exception as e:
                logger.error(f"[DatabaseService] Error seeding benchmark records: {e}")

    try:
        conn.commit()
    finally:
        conn.close()


def generate_sha256_audit_hash(event_data: Dict[str, Any], prev_hash: str) -> str:
    """Generates an immutable cryptographic SHA-256 hash chaining event payload with the previous hash."""
    canonical_payload = json.dumps(event_data, sort_keys=True)
    chain_input = f"{canonical_payload}|{prev_hash}".encode("utf-8")
    return hashlib.sha256(chain_input).hexdigest()
