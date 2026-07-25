from datetime import datetime

from content_agent import generate_product_content


def generate_and_save_content(db, product):

    if product.ai_analyzed_at is None:
        raise ValueError(
            "The product must be analyzed before "
            "content can be generated."
        )

    result = generate_product_content(
        product
    )

    product.public_title = result["title"]
    product.public_slug = result["slug"]
    product.public_summary = result["summary"]
    product.public_content = result["content"]

    product.content_status = "DRAFT"

    product.content_generated_at = (
        datetime.utcnow()
    )

    db.commit()
    db.refresh(product)

    return product, result["usage"]
