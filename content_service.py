from datetime import datetime

from content_agent import generate_product_article


def generate_and_save_content(db, product):
    if product.ai_analyzed_at is None:
        raise ValueError(
            "Product must be analyzed before generating content."
        )

    analysis = {
        "ai_score": product.ai_score,
        "decision": product.ai_decision,
        "target_audience": product.target_audience,
        "content_potential": product.content_potential,
        "best_content_angle": product.best_content_angle,
        "why_it_could_sell": product.why_it_could_sell,
        "risks": product.risks,
        "verification_needed": product.verification_needed,
    }

    product_data = {
        "name": product.title,
        "marketplace": product.platform,
        "price": product.price,
        "original_price": product.original_price,
        "rating": product.rating,
        "orders": product.orders,
        "category": product.category,
    }

    generated = generate_product_article(
        product_data,
        analysis,
    )

    product.slug = generated["slug"]
    product.article_title = generated["article_title"]
    product.article_content = generated["article_content"]
    product.publish_status = generated["publish_status"]
    product.content_generated_at = datetime.utcnow()

    db.commit()
    db.refresh(product)

    return generated
