"""
SourceScout Cross-Marketplace Opportunity Engine V1.

Purpose:
- Prepare products for comparison across marketplaces.
- Measure listing similarity.
- Estimate cross-marketplace opportunity.
- Remain provider-independent.

This module does NOT call marketplace APIs directly.
"""


import re
from difflib import SequenceMatcher


STOP_WORDS = {
    "new",
    "hot",
    "sale",
    "selling",
    "wholesale",
    "factory",
    "supplier",
    "custom",
    "customized",
    "product",
    "products",
    "for",
    "with",
    "and",
    "the",
    "a",
    "an",
}


def normalize_title(title):
    """
    Normalize a marketplace product title for
    cross-marketplace comparison.
    """

    text = str(
        title or ""
    ).lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text,
    )

    words = [
        word
        for word in text.split()
        if (
            word not in STOP_WORDS
            and len(word) > 1
        )
    ]

    return " ".join(
        words
    )


def get_title_tokens(title):

    normalized = normalize_title(
        title
    )

    return set(
        normalized.split()
    )


def calculate_product_similarity(
    source_product,
    candidate_product,
):
    """
    Calculate product similarity from 0 to 100.

    Uses:
    - normalized title sequence similarity
    - keyword/token overlap
    """

    source_title = normalize_title(
        source_product.get(
            "title",
            ""
        )
    )

    candidate_title = normalize_title(
        candidate_product.get(
            "title",
            ""
        )
    )


    if (
        not source_title
        or not candidate_title
    ):

        return 0.0


    sequence_score = (
        SequenceMatcher(
            None,
            source_title,
            candidate_title,
        ).ratio()
        * 100
    )


    source_tokens = get_title_tokens(
        source_title
    )

    candidate_tokens = get_title_tokens(
        candidate_title
    )


    union = (
        source_tokens
        | candidate_tokens
    )


    if union:

        token_score = (
            len(
                source_tokens
                & candidate_tokens
            )
            / len(union)
            * 100
        )

    else:

        token_score = 0


    final_score = (
        sequence_score * 0.40
        + token_score * 0.60
    )


    return round(
        final_score,
        2,
    )


def find_best_marketplace_match(
    source_product,
    marketplace_candidates,
):
    """
    Find the most similar candidate from another
    marketplace.
    """

    best_match = None
    best_similarity = 0.0


    for candidate in (
        marketplace_candidates
        or []
    ):

        similarity = (
            calculate_product_similarity(
                source_product,
                candidate,
            )
        )


        if similarity > best_similarity:

            best_similarity = similarity
            best_match = candidate


    return {
        "match": best_match,
        "similarity_score": round(
            best_similarity,
            2,
        ),
    }


def calculate_cross_marketplace_opportunity(
    source_product,
    comparison_result,
):
    """
    Estimate opportunity from 0 to 100.

    A high score means:
    - the source product has meaningful demand
    - a reasonably similar product exists elsewhere
    - the comparison-marketplace listing appears less
      established than the source listing

    This is an opportunity heuristic, not proof of
    market demand.
    """

    source_orders = int(
        source_product.get(
            "orders",
            0,
        )
        or 0
    )


    match = comparison_result.get(
        "match"
    )


    similarity = float(
        comparison_result.get(
            "similarity_score",
            0,
        )
        or 0
    )


    if not match:

        return 0.0


    target_orders = int(
        match.get(
            "orders",
            0,
        )
        or 0
    )


    score = 0.0


    # ------------------------------------------
    # Source demand — max 35
    # ------------------------------------------

    if source_orders >= 5000:
        score += 35

    elif source_orders >= 1000:
        score += 30

    elif source_orders >= 500:
        score += 25

    elif source_orders >= 100:
        score += 18

    elif source_orders >= 20:
        score += 10

    elif source_orders > 0:
        score += 5


    # ------------------------------------------
    # Product similarity — max 35
    # ------------------------------------------

    if similarity >= 80:
        score += 35

    elif similarity >= 70:
        score += 30

    elif similarity >= 60:
        score += 24

    elif similarity >= 50:
        score += 15

    elif similarity >= 40:
        score += 8


    # ------------------------------------------
    # Exposure gap — max 30
    # ------------------------------------------

    if source_orders > 0:

        exposure_ratio = (
            target_orders
            / source_orders
        )


        if exposure_ratio <= 0.05:
            score += 30

        elif exposure_ratio <= 0.15:
            score += 25

        elif exposure_ratio <= 0.30:
            score += 20

        elif exposure_ratio <= 0.60:
            score += 12

        elif exposure_ratio < 1:
            score += 5


    return round(
        min(
            score,
            100,
        ),
        2,
    )


def get_cross_marketplace_status(
    similarity_score,
):

    if similarity_score >= 60:
        return "matched"

    if similarity_score >= 40:
        return "candidate_found"

    return "not_found"
