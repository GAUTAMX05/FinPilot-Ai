# -*- coding: utf-8 -*-
"""Copy local SQLite data -> Postgres DATABASE_URL (idempotent, never deletes)."""
import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app.core.database import DB_PATH, init_db, is_postgres  # noqa: E402

TABLES_IN_ORDER = [
    "benchmark_records",
    "reconciliation_runs",
    "reconciliation_items",
    "controller_exceptions",
    "controller_approvals",
    "controller_audit_events",
    "evaluation_metrics",
]
# Conflict targets for ON CONFLICT DO NOTHING (None = plain insert, e.g. autoincrement logs)
CONFLICT_COL = {
    "benchmark_records": "(record_id)",
    "reconciliation_runs": "(run_id)",
    "reconciliation_items": None,
    "controller_exceptions": "(exception_id)",
    "controller_approvals": "(approval_id)",
    "controller_audit_events": None,
    "evaluation_metrics": "(run_id)",
}


def main() -> int:
    if not is_postgres():
        print("DATABASE_URL is not Postgres. Set DATABASE_URL first. Nothing done.")
        return 2
    if not os.path.exists(DB_PATH):
        print(f"No SQLite file at {DB_PATH}. Nothing to migrate (fresh Postgres seed will run).")
        return 0
    init_db()  # ensure Postgres schema exists
    import psycopg2
    from src.app.core.database import _ensure_sslmode

    src = sqlite3.connect(DB_PATH)
    src.row_factory = sqlite3.Row
    dst = psycopg2.connect(_ensure_sslmode(os.environ["DATABASE_URL"]))
    dst.autocommit = False
    total = 0
    try:
        for table in TABLES_IN_ORDER:
            rows = [dict(r) for r in src.execute(f"SELECT * FROM {table}").fetchall()]
            if not rows:
                print(f"{table}: 0 rows, skip")
                continue
            cols = list(rows[0].keys())
            # Drop SQLite-only 'id' None handling? Keep as-is; Postgres SERIAL accepts explicit ints.
            placeholders = ",".join(["%s"] * len(cols))
            collist = ",".join(cols)
            conflict = CONFLICT_COL.get(table)
            suffix = f" ON CONFLICT {conflict} DO NOTHING" if conflict else ""
            sql = f"INSERT INTO {table} ({collist}) VALUES ({placeholders}){suffix}"
            cur = dst.cursor()
            ok = 0
            for r in rows:
                try:
                    cur.execute(sql, [r[c] for c in cols])
                    ok += 1
                except Exception as e:
                    print(f"{table}: skip 1 row ({e})".split("\n")[0])
                    dst.rollback()
                    cur = dst.cursor()
            dst.commit()
            print(f"{table}: copied {ok}/{len(rows)}")
            total += ok
    finally:
        src.close()
        dst.close()
    print(f"Done. Total rows copied (attempted): {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
