from database import SessionLocal
from models import Product

from content_scoring import (
    calculate_content_opportunity_score,
    get_content_opportunity_level,
    calculate_combined_priority_score,
)


db = SessionLocal()

try:

    products = (
        db.query(Product)
        .all()
    )


    for product in products:

        content_score = (
            calculate_content_opportunity_score(
                product
            )
        )

        content_level = (
            get_content_opportunity_level(
                content_score
            )
        )

        combined_score = (
            calculate_combined_priority_score(
                product.opportunity_score,
                content_score,
            )
        )


        product.content_opportunity_score = (
            content_score
        )

        product.content_opportunity_level = (
            content_level
        )

        product.combined_priority_score = (
            combined_score
        )


        print(
            f"{product.id}: "
            f"Product={product.opportunity_score} | "
            f"Content={content_score} "
            f"({content_level}) | "
            f"Priority={combined_score} | "
            f"{product.title}"
        )


    db.commit()


finally:

    db.close()


print()
print(
    "✅ Content opportunity scores backfilled."
)
