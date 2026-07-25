"""
SourceScout Scoring Compatibility Layer

This module preserves the original public API while delegating
all Opportunity Score calculations to the unified
core.scoring_engine implementation.

Existing code can continue to import:

    from scoring import calculate_opportunity_score

without modification.
"""

from core.scoring_engine import calculate_opportunity_score as _core_calculate


def calculate_opportunity_score(product):
    """
    Compatibility wrapper for SQLAlchemy Product objects.

    Returns:
        float: Opportunity Score (0–100)
    """

    data = {
        "orders": product.orders,
        "rating": product.rating,
        "review_count": product.review_count,
        "supplier": product.supplier,
        "supplier_score": product.supplier_score,
        "commission_rate": product.commission_rate,
        "price": product.price,
        "price_min": product.price_min,
        "moq": product.moq,
    }

    result = _core_calculate(data)

    return result["opportunity_score"]
