import sqlite3


DB_PATH = "data/scout.db"


FIELDS = {
    "content_opportunity_score":
        "REAL DEFAULT 0",

    "content_opportunity_level":
        "TEXT",

    "combined_priority_score":
        "REAL DEFAULT 0",
}


conn = sqlite3.connect(
    DB_PATH
)

try:

    existing_columns = {
        row[1]
        for row in conn.execute(
            "PRAGMA table_info(products)"
        ).fetchall()
    }


    for field, definition in FIELDS.items():

        if field in existing_columns:

            print(
                f"⏭️ {field} already exists."
            )

            continue


        conn.execute(
            f"""
            ALTER TABLE products
            ADD COLUMN {field} {definition}
            """
        )

        print(
            f"✅ Added {field}"
        )


    conn.commit()


finally:

    conn.close()


print(
    "✅ Content scoring migration completed."
)
