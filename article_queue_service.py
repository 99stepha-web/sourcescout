from database import SessionLocal
from models import Product


def normalize_decision(value):
    """
    Normalize Claude decision values so values such as
    APPROVE, approved, or ' APPROVE ' are treated equally.
    """
    return str(value or "").strip().upper()


def get_article_queue():
    """
    Return Claude-approved products that do not yet have
    generated publishing article content.
    """

    db = SessionLocal()

    try:
        products = (
            db.query(Product)
            .filter(
                Product.ai_decision.isnot(None)
            )
            .order_by(
                Product.ai_score.desc()
            )
            .all()
        )

        queue = []

        for product in products:

            ai_decision = normalize_decision(
                product.ai_decision
            )

            editorial_decision = normalize_decision(
                product.editorial_decision
            )

            is_claude_approved = (
                ai_decision == "APPROVE"
            )

            is_editorially_approved = (
                ai_decision == "REVIEW"
                and editorial_decision == "APPROVE"
            )

            if not (
                is_claude_approved
                or is_editorially_approved
            ):
                continue

            if product.article_content:
                continue

            queue.append(
                product
            )

        return queue

    finally:
        db.close()


def get_review_queue():
    """
    Return products Claude marked for REVIEW.
    """

    db = SessionLocal()

    try:
        products = (
            db.query(Product)
            .filter(
                Product.ai_decision.isnot(None)
            )
            .order_by(
                Product.ai_score.desc()
            )
            .all()
        )

        return [
            product
            for product in products
            if (
                normalize_decision(
                    product.ai_decision
                ) == "REVIEW"
                and normalize_decision(
                    product.editorial_decision
                ) not in (
                    "APPROVE",
                    "REJECT",
                )
            )
        ]

    finally:
        db.close()


def get_rejected_products():
    """
    Return products rejected by Claude.
    """

    db = SessionLocal()

    try:
        products = (
            db.query(Product)
            .filter(
                Product.ai_decision.isnot(None)
            )
            .all()
        )

        return [
            product
            for product in products
            if normalize_decision(
                product.ai_decision
            ) == "REJECT"
        ]

    finally:
        db.close()
