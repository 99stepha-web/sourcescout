import json
import sqlite3
from pathlib import Path

from content_agent import generate_product_article


DB_PATH = Path("data/scout.db")


def get_product_for_publishing(product_id):
    """
    Load a product and its saved Claude analysis from SQLite.
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM products
        WHERE id = ?
        """,
        (product_id,),
    )

    row = cursor.fetchone()

    conn.close()

    if row is None:
        raise ValueError(
            f"Product with ID {product_id} was not found."
        )

    product = dict(row)

    product_data = {
        "name": product.get("title", ""),
        "marketplace": product.get("platform", ""),
        "price": product.get("price", ""),
        "original_price": product.get(
            "original_price",
            "",
        ),
        "rating": product.get("rating", ""),
        "orders": product.get("orders", ""),
        "category": product.get("category", ""),

        # IMPORTANT:
        # Real Taobao affiliate URL from SQLite.
        "affiliate_url": product.get(
            "affiliate_url",
            "",
        ),
    }

    analysis_data = {
        "ai_score": product.get("ai_score", ""),
        "decision": product.get("ai_decision", ""),
        "target_audience": product.get(
            "target_audience",
            "",
        ),
        "content_potential": product.get(
            "content_potential",
            "",
        ),
        "best_content_angle": product.get(
            "best_content_angle",
            "",
        ),
        "why_it_could_sell": product.get(
            "why_it_could_sell",
            "",
        ),
        "risks": product.get("risks", ""),
        "verification_needed": product.get(
            "verification_needed",
            "",
        ),
    }

    return (
        product,
        product_data,
        analysis_data,
    )


def save_generated_article(
    product_id,
    generated,
):
    """
    Permanently save generated article data into SQLite.
    """

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE products
        SET
            slug = ?,
            article_title = ?,
            article_content = ?,
            publish_status = ?
        WHERE id = ?
        """,
        (
            generated["slug"],
            generated["article_title"],
            generated["article_content"],
            generated["publish_status"],
            product_id,
        ),
    )

    conn.commit()

    updated_rows = cursor.rowcount

    conn.close()

    if updated_rows == 0:
        raise ValueError(
            "Article was generated but the product "
            "could not be updated."
        )


def generate_and_save_article(product_id):
    """
    Complete publishing-content workflow:

    1. Load product.
    2. Verify Claude analysis exists.
    3. Load real affiliate URL.
    4. Generate editorial article.
    5. Save article permanently.
    6. Return generated content + affiliate URL.
    """

    (
        raw_product,
        product_data,
        analysis_data,
    ) = get_product_for_publishing(
        product_id
    )

    if not raw_product.get(
        "ai_analyzed_at"
    ):
        raise ValueError(
            "This product must be analyzed with Claude "
            "before generating an article."
        )

    affiliate_url = (
        raw_product.get(
            "affiliate_url",
            "",
        )
        or ""
    ).strip()

    if not affiliate_url:

        raise ValueError(
            "Product does not have an affiliate URL."
        )

    # Only allow real Taobao affiliate URLs.
    if not (
        "m.tb.cn/" in affiliate_url
        or "s.click.taobao.com/" in affiliate_url
    ):
        raise ValueError(
            "Product affiliate_url is not a valid "
            "Taobao affiliate URL: "
            f"{affiliate_url}"
        )

    generated = generate_product_article(
        product_data,
        analysis_data,
    )

    save_generated_article(
        product_id,
        generated,
    )

    article_sections = json.loads(
        generated["article_content"]
    )

    return {
        "product_id": product_id,
        "slug": generated["slug"],
        "article_title": generated[
            "article_title"
        ],
        "article": article_sections,
        "affiliate_url": affiliate_url,
        "publish_status": generated[
            "publish_status"
        ],
        "usage": generated["usage"],
    }
