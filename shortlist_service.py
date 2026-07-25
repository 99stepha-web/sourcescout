from database import SessionLocal
from models import Product


DEFAULT_SHORTLIST_THRESHOLD = 60
DEFAULT_PRIORITY_THRESHOLD = 65


def get_shortlisted_products(
    threshold=DEFAULT_SHORTLIST_THRESHOLD,
    priority_threshold=DEFAULT_PRIORITY_THRESHOLD,
    only_unanalyzed=True,
):
    """
    Return products that meet the opportunity-score
    threshold and are candidates for Claude analysis.
    """

    db = SessionLocal()

    try:
        query = (
            db.query(Product)
            .filter(
                Product.opportunity_score >= threshold,
                Product.combined_priority_score
                >= priority_threshold,
            )
        )

        if only_unanalyzed:
            query = query.filter(
                Product.ai_analyzed_at.is_(None)
            )

        products = (
            query
            .order_by(
                Product.combined_priority_score.desc(),
                Product.opportunity_score.desc(),
            )
            .all()
        )

        return products

    finally:
        db.close()


def get_shortlist_count(
    threshold=DEFAULT_SHORTLIST_THRESHOLD,
    priority_threshold=DEFAULT_PRIORITY_THRESHOLD,
):
    """
    Count unanalyzed products above the threshold.
    """

    db = SessionLocal()

    try:
        return (
            db.query(Product)
            .filter(
                Product.opportunity_score >= threshold,
                Product.combined_priority_score
                >= priority_threshold,
                Product.ai_analyzed_at.is_(None),
            )
            .count()
        )

    finally:
        db.close()
