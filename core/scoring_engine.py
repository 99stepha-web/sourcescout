"""
SourceScout Core Scoring Engine

Single source of truth for marketplace scoring.

This implementation preserves the production Opportunity Score
algorithm while exposing scoring signals for future explainability.
"""

import re

from utils.data_cleaning import (
    clean_float,
    clean_int,
    clean_text,
)


def calculate_opportunity_score(data):
    score = 0.0
    signals = {}

    orders = clean_int(data.get("orders"))
    rating = clean_float(data.get("rating"))
    review_count = clean_int(data.get("review_count"))
    supplier = clean_text(data.get("supplier"))
    supplier_score = clean_float(data.get("supplier_score"))
    commission_rate = clean_float(data.get("commission_rate"))

    price = clean_float(
        data.get(
            "price_min",
            data.get("price"),
        )
    )

    moq = clean_text(
        data.get("moq")
    ).lower()

    # --------------------------------------------------
    # Demand (30)
    # --------------------------------------------------

    if orders >= 10000:
        demand = 30
    elif orders >= 5000:
        demand = 27
    elif orders >= 1000:
        demand = 23
    elif orders >= 500:
        demand = 19
    elif orders >= 100:
        demand = 14
    elif orders >= 20:
        demand = 8
    elif orders > 0:
        demand = 4
    else:
        demand = 0

    score += demand
    signals["demand"] = demand

    # --------------------------------------------------
    # Rating + Reviews (25)
    # --------------------------------------------------

    if rating >= 4.8:
        rating_points = 18
    elif rating >= 4.5:
        rating_points = 15
    elif rating >= 4.0:
        rating_points = 10
    elif rating > 0:
        rating_points = 4
    else:
        rating_points = 0

    if review_count >= 500:
        review_points = 7
    elif review_count >= 100:
        review_points = 6
    elif review_count >= 20:
        review_points = 4
    elif review_count >= 5:
        review_points = 2
    elif review_count > 0:
        review_points = 1
    else:
        review_points = 0

    score += rating_points + review_points
    signals["rating"] = rating_points
    signals["reviews"] = review_points

    # --------------------------------------------------
    # Supplier (15)
    # --------------------------------------------------

    if supplier_score >= 90:
        supplier_points = 15
    elif supplier_score >= 80:
        supplier_points = 13
    elif supplier_score >= 70:
        supplier_points = 10
    elif supplier_score > 0:
        supplier_points = 6
    elif supplier:
        supplier_points = 5
    else:
        supplier_points = 0

    score += supplier_points
    signals["supplier"] = supplier_points

    # --------------------------------------------------
    # Price (15)
    # --------------------------------------------------

    unit_pricing_terms = (
        "watt",
        "watts",
        "meter",
        "meters",
        "kilogram",
        "kilograms",
        "kg",
        "ton",
        "tons",
    )

    has_unit_pricing = any(
        term in moq
        for term in unit_pricing_terms
    )

    if has_unit_pricing:
        price_points = 3
    elif 10 <= price <= 100:
        price_points = 15
    elif 100 < price <= 300:
        price_points = 12
    elif 300 < price <= 1000:
        price_points = 8
    elif price > 1000:
        price_points = 4
    elif 0 < price < 10:
        price_points = 6
    else:
        price_points = 0

    score += price_points
    signals["price"] = price_points

    # --------------------------------------------------
    # MOQ (10)
    # --------------------------------------------------

    moq_match = re.search(
        r"\d+(?:\.\d+)?",
        moq,
    )

    if has_unit_pricing:
        moq_points = 2

    elif moq_match:

        qty = float(moq_match.group())

        if qty <= 1:
            moq_points = 10
        elif qty <= 5:
            moq_points = 8
        elif qty <= 20:
            moq_points = 6
        elif qty <= 100:
            moq_points = 4
        else:
            moq_points = 2

    else:
        moq_points = 3

    score += moq_points
    signals["moq"] = moq_points

    # --------------------------------------------------
    # Commission (5)
    # --------------------------------------------------

    if commission_rate >= 15:
        commission_points = 5
    elif commission_rate >= 10:
        commission_points = 4
    elif commission_rate >= 5:
        commission_points = 3
    elif commission_rate > 0:
        commission_points = 1
    else:
        commission_points = 0

    score += commission_points
    signals["commission"] = commission_points

    score = round(min(max(score, 0), 100), 1)

    return {
        "opportunity_score": score,
        "signals": signals,
    }
