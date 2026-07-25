from database import SessionLocal
from models import Product


def get_products_missing_affiliate_links():
    """
    Return products that are relevant to publishing
    but do not yet have an affiliate tracking URL.
    """

    db = SessionLocal()

    try:

        products = (
            db.query(Product)
            .filter(
                Product.article_content.isnot(None)
            )
            .order_by(
                Product.opportunity_score.desc()
            )
            .all()
        )

        return [
            product
            for product in products
            if not str(
                product.affiliate_url or ""
            ).strip()
        ]

    finally:

        db.close()


def save_affiliate_url(
    product_id,
    affiliate_url,
):
    """
    Save an affiliate tracking URL without modifying
    the original marketplace product URL.
    """

    affiliate_url = str(
        affiliate_url or ""
    ).strip()


    if not affiliate_url:

        raise ValueError(
            "Affiliate URL cannot be empty."
        )


    if not affiliate_url.startswith(
        ("http://", "https://")
    ):

        raise ValueError(
            "Affiliate URL must begin with "
            "http:// or https://"
        )


    db = SessionLocal()

    try:

        product = (
            db.query(Product)
            .filter(
                Product.id == product_id
            )
            .first()
        )


        if not product:

            raise ValueError(
                f"Product {product_id} was not found."
            )


        product.affiliate_url = (
            affiliate_url
        )


        db.commit()

        db.refresh(
            product
        )


        return {
            "product_id": product.id,
            "product_url": product.product_url,
            "affiliate_url": product.affiliate_url,
        }


    except Exception:

        db.rollback()

        raise


    finally:

        db.close()


def has_affiliate_url(product):
    """
    Check whether a product has an affiliate URL.
    """

    return bool(
        str(
            product.affiliate_url or ""
        ).strip()
    )
