"""
Product opportunity scoring and hard filtering.

Implements the Stage A (hard filter) and Stage B (opportunity
ranking) of the discovery pipeline:

    candidates -> hard_filter() -> survivors -> calculate_selection_score()
    -> ranked -> top N sent to Claude

Every function accepts a plain dict-like "product" (works with both
SQLAlchemy Product rows via a small adapter and raw dicts, see
`as_dict`) and never invents a value: a missing marketplace metric is
treated as LOW CONFIDENCE evidence, not as zero and not as a guess.

Weights and thresholds live in config/intelligence.py (SELECTION_CONFIG)
— nothing here should need to change if a threshold changes.
"""

import math
import re

from config.intelligence import SELECTION_CONFIG
from category_relevance import relevance_score

BADGE_KEYWORDS = [
    "月销", "销量", "已售", "付款人数", "成交",
    "热销", "爆款", "热门", "趋势", "推荐", "新品",
    "高转化", "高佣", "优质商家", "优选", "热卖",
    "种草", "同类热推", "店内高佣",
]

RESTRICTED_KEYWORDS = [
    "处方", "药品", "医疗器械", "枪", "弹药", "麻醉",
]


def as_dict(product):
    """Normalize a SQLAlchemy Product row or dict into a plain dict."""

    if isinstance(product, dict):
        return product

    return {
        column.name: getattr(product, column.name)
        for column in product.__table__.columns
    }


def extract_badges(text):
    """Return the subset of BADGE_KEYWORDS literally present in text."""

    text = text or ""
    return [kw for kw in BADGE_KEYWORDS if kw in text]


def _band_score(value, bands):
    for threshold, score in bands:
        if value <= threshold:
            return float(score)

    return 100.0


def sales_score(product):
    monthly = product.get("monthly_sales")
    orders = product.get("orders")

    value = monthly if monthly is not None else orders

    if value is None:
        return None, "LOW", "no sales/orders data available"

    if value <= 0:
        badges = extract_badges(product.get("badges") or "")
        if badges:
            return 20.0, "LOW", f"zero recorded sales but trend badges present: {', '.join(badges)}"
        return 5.0, "MEDIUM", "zero recorded sales, no trend evidence"

    score = _band_score(value, SELECTION_CONFIG["sales_bands"])
    source = "monthly_sales" if monthly is not None else "orders"

    return score, "HIGH", f"{source}={value}"


def feedback_score(product):
    rating = product.get("rating")
    review_count = product.get("review_count")

    if rating is None and not review_count:
        return None, "LOW", "no rating/review data exposed by marketplace"

    if rating is not None and review_count:
        # Bayesian shrinkage: pull the raw rating toward a neutral
        # prior (3.8/5) with strength proportional to how few
        # reviews back it up, so 5.0/3 reviews can't outrank
        # 4.8/2000 reviews.
        prior_rating = 3.8
        prior_weight = 20

        shrunk = (
            (rating * review_count) + (prior_rating * prior_weight)
        ) / (review_count + prior_weight)

        rating_component = max(0.0, min(100.0, (shrunk / 5.0) * 100))
        volume_component = _band_score(
            review_count, SELECTION_CONFIG["review_count_bands"]
        )

        score = round(rating_component * 0.6 + volume_component * 0.4, 1)

        return score, "HIGH", f"rating={rating} shrunk to {shrunk:.2f} over {review_count} reviews"

    if review_count:
        volume_component = _band_score(
            review_count, SELECTION_CONFIG["review_count_bands"]
        )
        return volume_component * 0.7, "MEDIUM", f"review_count={review_count}, no rating exposed"

    return None, "LOW", "rating present but no review volume to weight it"


def trend_momentum_score(product, history=None):
    reasons = []
    score = None

    if product.get("trend_score") is not None:
        score = float(product["trend_score"])
        reasons.append(f"trend_score={score}")

    badges = extract_badges(product.get("badges") or "")

    if badges:
        badge_score = min(100.0, 30.0 + 10.0 * len(badges))
        score = badge_score if score is None else max(score, badge_score)
        reasons.append(f"badges: {', '.join(badges)}")

    if history and len(history) >= 2:
        previous = history[-2].get("monthly_sales")
        current = history[-1].get("monthly_sales")

        if previous is not None and current is not None and previous > 0:
            growth = (current - previous) / previous
            momentum_score = max(0.0, min(100.0, 50.0 + growth * 100))
            score = momentum_score if score is None else max(score, momentum_score)
            reasons.append(f"sales growth {growth:+.0%} vs previous snapshot")

    if score is None:
        return None, "LOW", "no trend badges, trend_score, or history available"

    confidence = "HIGH" if history else ("MEDIUM" if badges else "LOW")

    return round(score, 1), confidence, "; ".join(reasons)


def commission_score(product):
    rate = product.get("commission_rate")
    price = product.get("price")
    amount = product.get("commission_amount")

    if rate is None:
        return None, "LOW", "no commission data available"

    if amount is None and price:
        amount = price * (rate / 100.0)

    rate_component = min(100.0, (rate / 15.0) * 100)

    if amount is not None:
        amount_component = min(100.0, math.log1p(max(amount, 0)) / math.log1p(20) * 100)
        score = round(rate_component * 0.5 + amount_component * 0.5, 1)
        reason = f"commission_rate={rate}%, est. commission={amount:.2f}"
    else:
        score = round(rate_component, 1)
        reason = f"commission_rate={rate}% (no price to estimate per-sale amount)"

    return score, "HIGH" if amount is not None else "MEDIUM", reason


def supplier_quality_score(product):
    supplier_score = product.get("supplier_score")
    shop_rating = product.get("shop_rating")

    if supplier_score:
        return min(100.0, float(supplier_score)), "HIGH", f"supplier_score={supplier_score}"

    if shop_rating:
        return min(100.0, (shop_rating / 5.0) * 100), "MEDIUM", f"shop_rating={shop_rating}"

    return None, "LOW", "no supplier/shop quality signal available"


def price_competitiveness_score(product):
    percentile = product.get("price_percentile")

    if percentile is None:
        return None, "LOW", "no category price percentile available"

    # Marketplace reports "price is lower than X% of the category" —
    # higher percentile means cheaper relative to peers. Reward that,
    # but don't reward extreme percentiles more than moderate ones
    # (suspiciously cheap is not more "competitive").
    score = min(100.0, percentile * 1.1)

    return round(score, 1), "HIGH", f"cheaper than {percentile}% of comparable listings"


def content_potential_score(product, category_score):
    title = product.get("title") or ""

    length_component = min(100.0, len(title) / 40 * 100)
    category_component = category_score

    score = round(length_component * 0.4 + category_component * 0.6, 1)

    return score, "MEDIUM", f"title_length={len(title)}, category_relevance={category_score}"


def hard_filter(product, category_score):
    """
    Deterministic reject/pass. Returns (passed: bool, reasons: list[str]).
    """

    cfg = SELECTION_CONFIG["hard_filter"]
    reasons = []
    title = (product.get("title") or "")

    if any(word in title for word in RESTRICTED_KEYWORDS):
        return False, ["restricted/sensitive product category"]

    if category_score < cfg["min_category_relevance"]:
        return False, [
            f"category relevance {category_score:.0f} below minimum "
            f"{cfg['min_category_relevance']}"
        ]

    commission_rate = product.get("commission_rate")
    monthly = product.get("monthly_sales")
    orders = product.get("orders")
    sales_value = monthly if monthly is not None else orders
    badges = extract_badges(product.get("badges") or "")

    has_trend_evidence = bool(badges) or (product.get("trend_score") or 0) > 0

    low_commission = (
        commission_rate is not None
        and commission_rate < cfg["min_commission_rate"]
    )

    no_sales_evidence = (
        sales_value is not None
        and sales_value < cfg["min_sales_without_trend_evidence"]
        and not has_trend_evidence
    )

    if low_commission and no_sales_evidence:
        reasons.append(
            f"commission {commission_rate}% below minimum "
            f"{cfg['min_commission_rate']}% AND no sales/trend evidence"
        )

    no_rating = product.get("rating") is None
    no_reviews = not product.get("review_count")

    if (
        sales_value is not None
        and sales_value < cfg["min_sales_without_trend_evidence"]
        and no_rating
        and no_reviews
        and not has_trend_evidence
    ):
        reasons.append(
            "extremely low sales AND no reviews AND no rating AND no trend evidence"
        )

    if reasons:
        return False, reasons

    return True, []


def calculate_selection_score(product, keyword, history=None):
    """
    Full Stage A + Stage B evaluation for one product.

    Returns a dict: total score, per-factor breakdown (score,
    confidence, reason), category relevance, hard-filter outcome, and
    a human-readable list of reasons suitable for CLI/Claude-prompt
    display.
    """

    product = as_dict(product)
    weights = SELECTION_CONFIG["weights"]

    cat_score, cat_reason = relevance_score(keyword, product.get("title") or "")

    passed_filter, filter_reasons = hard_filter(product, cat_score)

    factors = {
        "sales": sales_score(product),
        "feedback": feedback_score(product),
        "trend": trend_momentum_score(product, history),
        "commission": commission_score(product),
        "supplier": supplier_quality_score(product),
        "price": price_competitiveness_score(product),
        "content": content_potential_score(product, cat_score),
    }

    total = 0.0
    reasons = []
    breakdown = {}

    for name, (score, confidence, reason) in factors.items():
        weight = weights[name]

        if score is None:
            # Missing evidence contributes 0 to the weighted total
            # (never guessed), and is called out explicitly.
            breakdown[name] = {
                "score": None,
                "confidence": confidence,
                "reason": reason,
            }
            reasons.append(f"{name}: no data ({reason})")
            continue

        total += score * weight

        breakdown[name] = {
            "score": round(score, 1),
            "confidence": confidence,
            "reason": reason,
        }

        reasons.append(f"{name}={score:.0f} ({confidence}): {reason}")

    total = round(total, 1)

    if cat_score < SELECTION_CONFIG["hard_filter"]["min_category_relevance"]:
        status = "CATEGORY_MISMATCH"
        reasons = filter_reasons + reasons
    elif not passed_filter:
        status = "HARD_FILTERED"
        reasons = filter_reasons + reasons
    elif total >= SELECTION_CONFIG["approval_thresholds"]["min_selection_score_for_claude"]:
        status = "RANKED"
    else:
        status = "LOW_PRIORITY"

    return {
        "selection_score": total,
        "selection_status": status,
        "selection_reason": "; ".join(reasons),
        "category_score": cat_score,
        "category_reason": cat_reason,
        "passed_hard_filter": passed_filter,
        "breakdown": breakdown,
    }


def deduplicate_candidates(products, keyword):
    """
    Collapse near-identical products (same product_id, or same
    normalized title) to the single strongest commercial candidate,
    scored with calculate_selection_score. Returns (survivors, dropped)
    where survivors keep the original product objects and dropped is
    a list of (product, reason) for products removed as duplicates.
    """

    def normalize(title):
        title = (title or "").lower()
        return re.sub(r"[\s\-_/,.，。！]+", "", title)

    groups = {}

    for product in products:
        d = as_dict(product)
        key = d.get("product_id") or normalize(d.get("title"))
        groups.setdefault(key, []).append(product)

    survivors = []
    dropped = []

    for key, group in groups.items():
        if len(group) == 1:
            survivors.append(group[0])
            continue

        scored = [
            (p, calculate_selection_score(p, keyword)["selection_score"])
            for p in group
        ]
        scored.sort(key=lambda pair: pair[1], reverse=True)

        survivors.append(scored[0][0])

        for product, score in scored[1:]:
            dropped.append((product, f"duplicate of stronger candidate (score {score})"))

    return survivors, dropped
