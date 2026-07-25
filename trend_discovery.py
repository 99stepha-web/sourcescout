"""
SourceScout Trend Discovery Engine V1.

Discovers potential product opportunities by running
multiple marketplace searches, merging the results,
removing duplicates, and ranking the candidates.

This module does NOT:
- import products
- call Claude
- publish content
"""


from marketplace_discovery import discover_products


DEFAULT_TREND_SEEDS = [
    "viral gadgets",
    "smart home gadgets",
    "portable travel gadgets",
    "beauty tools",
    "fitness accessories",
    "kitchen gadgets",
    "car accessories",
    "outdoor gadgets",
]


def calculate_candidate_trend_score(product):
    """
    Estimate marketplace trend strength from currently
    available discovery signals.

    Maximum score: 100.

    This is a candidate-stage score only. It does not
    replace the permanent Research Intelligence score.
    """

    orders = int(
        product.get(
            "orders",
            0,
        )
        or 0
    )

    rating = float(
        product.get(
            "rating",
            0,
        )
        or 0
    )

    review_count = int(
        product.get(
            "review_count",
            0,
        )
        or 0
    )

    score = 0.0


    # ------------------------------------------
    # Demand — maximum 55
    # ------------------------------------------

    if orders >= 5000:
        score += 55

    elif orders >= 2000:
        score += 50

    elif orders >= 1000:
        score += 45

    elif orders >= 500:
        score += 38

    elif orders >= 100:
        score += 28

    elif orders >= 20:
        score += 18

    elif orders > 0:
        score += 8


    # ------------------------------------------
    # Rating — maximum 25
    # ------------------------------------------

    if rating >= 4.8:
        score += 25

    elif rating >= 4.5:
        score += 20

    elif rating >= 4.0:
        score += 14

    elif rating > 0:
        score += 7


    # ------------------------------------------
    # Review evidence — maximum 10
    # ------------------------------------------

    if review_count >= 1000:
        score += 10

    elif review_count >= 500:
        score += 8

    elif review_count >= 100:
        score += 6

    elif review_count >= 20:
        score += 4

    elif review_count > 0:
        score += 2


    # ------------------------------------------
    # Listing completeness — maximum 10
    # ------------------------------------------

    if product.get(
        "image_url"
    ):
        score += 3


    if product.get(
        "product_url"
    ):
        score += 3


    if product.get(
        "supplier"
    ):
        score += 2


    if (
        product.get(
            "price"
        )
        or product.get(
            "price_min"
        )
    ):
        score += 2


    return round(
        min(
            score,
            100,
        ),
        2,
    )


def _candidate_identity(product):
    """
    Build a stable-enough identity for deduplication.
    """

    platform = str(
        product.get(
            "platform",
            ""
        )
        or ""
    ).strip().lower()

    product_id = str(
        product.get(
            "product_id",
            ""
        )
        or ""
    ).strip()

    product_url = str(
        product.get(
            "product_url",
            ""
        )
        or ""
    ).strip()

    title = str(
        product.get(
            "title",
            ""
        )
        or ""
    ).strip().lower()


    if product_id:

        return (
            platform,
            "id",
            product_id,
        )


    if product_url:

        return (
            platform,
            "url",
            product_url,
        )


    return (
        platform,
        "title",
        title,
    )


def discover_trend_candidates(
    marketplace="Alibaba",
    seed_keywords=None,
    results_per_seed=10,
    max_candidates=50,
):
    """
    Run multiple marketplace searches and return one
    deduplicated, ranked candidate list.
    """

    seeds = (
        seed_keywords
        or DEFAULT_TREND_SEEDS
    )


    unique_products = {}


    for seed in seeds:

        seed = str(
            seed
            or ""
        ).strip()


        if not seed:

            continue


        results = discover_products(
            marketplace=marketplace,
            keyword=seed,
            limit=results_per_seed,
        )


        for product in (
            results
            or []
        ):

            candidate = dict(
                product
            )


            candidate[
                "trend_seed"
            ] = seed


            candidate[
                "trend_score"
            ] = (
                calculate_candidate_trend_score(
                    candidate
                )
            )


            identity = (
                _candidate_identity(
                    candidate
                )
            )


            existing = (
                unique_products.get(
                    identity
                )
            )


            if (
                existing is None
                or candidate[
                    "trend_score"
                ]
                > existing[
                    "trend_score"
                ]
            ):

                unique_products[
                    identity
                ] = candidate


    candidates = list(
        unique_products.values()
    )


    candidates.sort(
        key=lambda product: (
            product.get(
                "trend_score",
                0,
            ),
            product.get(
                "orders",
                0,
            ),
            product.get(
                "rating",
                0,
            ),
        ),
        reverse=True,
    )


    return candidates[
        :max_candidates
    ]
