import sqlite3


DB_PATH = "data/scout.db"


FIELDS = {
    "research_keyword":
        "TEXT",

    "discovery_source":
        "TEXT",

    "source_product_url":
        "TEXT",

    "trend_score":
        "REAL DEFAULT 0",

    "video_potential_score":
        "REAL DEFAULT 0",

    "has_demo_video":
        "INTEGER DEFAULT 0",

    "cross_marketplace_status":
        "TEXT DEFAULT 'not_checked'",
}


conn = sqlite3.connect(
    DB_PATH
)

cursor = conn.cursor()


existing_columns = {
    row[1]
    for row in cursor.execute(
        "PRAGMA table_info(products)"
    ).fetchall()
}


for field_name, field_type in FIELDS.items():

    if field_name in existing_columns:

        print(
            f"⏭️ {field_name} already exists."
        )

        continue


    cursor.execute(
        f"""
        ALTER TABLE products
        ADD COLUMN {field_name} {field_type}
        """
    )


    print(
        f"✅ Added {field_name}"
    )


conn.commit()
conn.close()


print()
print(
    "✅ Trend research migration completed."
)
