import sqlite3
from datetime import datetime, timezone


DB_PATH = "data/scout.db"

# Keep pricing centralized so it can be updated without
# changing the automation workflow.
#
# These values should be verified against the current
# Anthropic pricing before relying on cost estimates.
INPUT_COST_PER_MILLION = 1.00
OUTPUT_COST_PER_MILLION = 5.00


def calculate_estimated_cost(
    input_tokens,
    output_tokens,
):
    input_cost = (
        input_tokens
        / 1_000_000
        * INPUT_COST_PER_MILLION
    )

    output_cost = (
        output_tokens
        / 1_000_000
        * OUTPUT_COST_PER_MILLION
    )

    return round(
        input_cost + output_cost,
        6,
    )


def ensure_automation_runs_table():
    conn = sqlite3.connect(DB_PATH)

    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS automation_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL DEFAULT 'running',

                analyzed_count INTEGER NOT NULL DEFAULT 0,
                approve_count INTEGER NOT NULL DEFAULT 0,
                review_count INTEGER NOT NULL DEFAULT 0,
                reject_count INTEGER NOT NULL DEFAULT 0,

                articles_generated INTEGER NOT NULL DEFAULT 0,
                failure_count INTEGER NOT NULL DEFAULT 0,

                input_tokens INTEGER NOT NULL DEFAULT 0,
                output_tokens INTEGER NOT NULL DEFAULT 0,
                estimated_cost_usd REAL NOT NULL DEFAULT 0,

                error_summary TEXT
            )
            """
        )

        conn.commit()

    finally:
        conn.close()


def start_automation_run():
    ensure_automation_runs_table()

    conn = sqlite3.connect(DB_PATH)

    try:
        cursor = conn.execute(
            """
            INSERT INTO automation_runs (
                started_at,
                status
            )
            VALUES (?, ?)
            """,
            (
                datetime.now(
                    timezone.utc
                ).isoformat(),
                "running",
            ),
        )

        conn.commit()

        return cursor.lastrowid

    finally:
        conn.close()


def complete_automation_run(
    run_id,
    analyzed_count=0,
    approve_count=0,
    review_count=0,
    reject_count=0,
    articles_generated=0,
    failure_count=0,
    input_tokens=0,
    output_tokens=0,
    error_summary=None,
):
    estimated_cost = calculate_estimated_cost(
        input_tokens,
        output_tokens,
    )

    if failure_count == 0:
        status = "completed"
    else:
        status = "partial"

    conn = sqlite3.connect(DB_PATH)

    try:
        conn.execute(
            """
            UPDATE automation_runs
            SET
                completed_at = ?,
                status = ?,
                analyzed_count = ?,
                approve_count = ?,
                review_count = ?,
                reject_count = ?,
                articles_generated = ?,
                failure_count = ?,
                input_tokens = ?,
                output_tokens = ?,
                estimated_cost_usd = ?,
                error_summary = ?
            WHERE id = ?
            """,
            (
                datetime.now(
                    timezone.utc
                ).isoformat(),
                status,
                analyzed_count,
                approve_count,
                review_count,
                reject_count,
                articles_generated,
                failure_count,
                input_tokens,
                output_tokens,
                estimated_cost,
                error_summary,
                run_id,
            ),
        )

        conn.commit()

    finally:
        conn.close()


def fail_automation_run(
    run_id,
    error_summary,
):
    conn = sqlite3.connect(DB_PATH)

    try:
        conn.execute(
            """
            UPDATE automation_runs
            SET
                completed_at = ?,
                status = ?,
                error_summary = ?
            WHERE id = ?
            """,
            (
                datetime.now(
                    timezone.utc
                ).isoformat(),
                "failed",
                str(error_summary),
                run_id,
            ),
        )

        conn.commit()

    finally:
        conn.close()


def get_automation_runs(limit=20):
    ensure_automation_runs_table()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        rows = conn.execute(
            """
            SELECT *
            FROM automation_runs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        conn.close()


def get_total_automation_cost():
    ensure_automation_runs_table()

    conn = sqlite3.connect(DB_PATH)

    try:
        row = conn.execute(
            """
            SELECT
                COALESCE(
                    SUM(estimated_cost_usd),
                    0
                )
            FROM automation_runs
            """
        ).fetchone()

        return float(row[0] or 0)

    finally:
        conn.close()
