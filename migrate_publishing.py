import sqlite3
from pathlib import Path

DB_PATH = Path("data/scout.db")

NEW_COLUMNS = {
    "slug": "TEXT",
    "affiliate_url": "TEXT",
    "image_url": "TEXT",
    "publish_status": "TEXT DEFAULT 'draft'",
    "article_title": "TEXT",
    "article_content": "TEXT",
    "published_at": "TEXT",
}


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(products)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    for column_name, column_type in NEW_COLUMNS.items():
        if column_name not in existing_columns:
            cursor.execute(
                f"ALTER TABLE products ADD COLUMN {column_name} {column_type}"
            )
            print(f"✅ Added: {column_name}")
        else:
            print(f"⏭️ Already exists: {column_name}")

    conn.commit()
    conn.close()

    print("\n🚀 Publishing database migration completed.")


if __name__ == "__main__":
    migrate()