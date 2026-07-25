from sqlalchemy import inspect, text

from database import engine


NEW_COLUMNS = {
    "ai_score": "FLOAT",
    "ai_decision": "VARCHAR(20)",
    "target_audience": "TEXT",
    "content_potential": "TEXT",
    "best_content_angle": "TEXT",
    "why_it_could_sell": "TEXT",
    "risks": "TEXT",
    "verification_needed": "TEXT",
    "ai_input_tokens": "INTEGER DEFAULT 0",
    "ai_output_tokens": "INTEGER DEFAULT 0",
    "ai_analyzed_at": "DATETIME",
    "public_title": "VARCHAR(500)",
    "public_slug": "VARCHAR(500)",
    "public_summary": "TEXT",
    "public_content": "TEXT",
    "content_status": "VARCHAR(50) DEFAULT 'NOT_CREATED'",
    "content_generated_at": "DATETIME",

}


def migrate():
    inspector = inspect(engine)

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("products")
    }

    with engine.begin() as connection:

        for column_name, column_type in NEW_COLUMNS.items():

            if column_name in existing_columns:
                print(f"⏭️ Already exists: {column_name}")
                continue

            connection.execute(
                text(
                    f"ALTER TABLE products "
                    f"ADD COLUMN {column_name} {column_type}"
                )
            )

            print(f"✅ Added: {column_name}")

    print("\n🚀 Database migration completed.")


if __name__ == "__main__":
    migrate()
