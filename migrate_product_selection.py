"""
Migration: product-selection intelligence fields.

Idempotent — follows the existing migrate_*.py convention in this
repo (PRAGMA table_info + ALTER TABLE ADD COLUMN, guarded per-column).

Adds:
  - raw marketplace signals not previously captured (commission
    amount, monthly sales, promotion-window counters, category
    percentiles, listing/discovery freshness)
  - the final selection decision fields (selection_score,
    selection_status, selection_reason)

Also creates product_metrics_history, a lightweight append-only table
for tracking a product's signals over time (needed for real trend/
momentum detection instead of guessing).
"""

import sqlite3

DB_PATH = "data/scout.db"

FIELDS = {
    "commission_amount": "REAL",
    "monthly_sales": "INTEGER",
    "monthly_promoters": "INTEGER",
    "today_sales": "INTEGER",
    "price_percentile": "REAL",
    "commission_percentile": "REAL",
    "shop_rating": "REAL",
    "listing_date": "TEXT",
    "subcategory": "TEXT",
    "sales_velocity": "REAL",
    "review_velocity": "REAL",
    "last_seen_at": "DATETIME",
    "last_metrics_update": "DATETIME",
    "selection_score": "REAL",
    "selection_status": "TEXT",
    "selection_reason": "TEXT",
    "badges": "TEXT",
}

HISTORY_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS product_metrics_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    captured_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    price REAL,
    commission_rate REAL,
    monthly_sales INTEGER,
    rating REAL,
    review_count INTEGER,
    supplier_score REAL,
    trend_score REAL,
    selection_score REAL,
    FOREIGN KEY (product_id) REFERENCES products (id)
)
"""

HISTORY_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_product_metrics_history_product_id
ON product_metrics_history (product_id, captured_at)
"""


def run():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    existing_columns = {
        row[1]
        for row in cursor.execute("PRAGMA table_info(products)").fetchall()
    }

    for field_name, field_type in FIELDS.items():
        if field_name in existing_columns:
            print(f"⏭️ {field_name} already exists.")
            continue

        cursor.execute(
            f"ALTER TABLE products ADD COLUMN {field_name} {field_type}"
        )

        print(f"✅ Added {field_name}")

    cursor.execute(HISTORY_TABLE_SQL)
    cursor.execute(HISTORY_INDEX_SQL)

    print("✅ product_metrics_history table ready")

    conn.commit()
    conn.close()

    print()
    print("✅ Product selection migration completed.")


if __name__ == "__main__":
    run()
