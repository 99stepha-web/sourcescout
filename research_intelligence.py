"""
SourceScout Research Intelligence Scoring V1.

This score measures the value of a product discovered
through targeted or trend research.

It does NOT replace:
- opportunity_score
- content_opportunity_score
- combined_priority_score

Maximum score: 100
"""


def calculate_research_intelligence_score(product):
    """
    Maximum score: 100

    Factors:
    - Research intent / targeted discovery: 20
    - Marketplace demand signal: 25
    - Trend signal: 20
    - Video / demonstration potential: 15
    - Product data confidence: 10
    - Cross-marketplace potential: 10
    """

    score = 0.0


    # ==================================================
    # 1. TARGETED RESEARCH INTENT — MAX 20
    # ==================================================

    research_keyword = str(
        getattr(
            product,
            "research_keyword",
            "",
        )
        or ""
    ).strip()

    discovery_source = str(
        getattr(
            product,
            "discovery_source",
            "",
        )
        or ""
    ).strip()


    if research_keyword and discovery_source:
        score += 20

    elif research_keyword:
        score += 15

    elif discovery_source:
        score += 10


    # ==================================================
    # 2. MARKETPLACE DEMAND — MAX 25
    # ==================================================

    orders = int(
        getattr(
            product,
            "orders",
            0,
        )
        or 0
    )


    if orders >= 5000:
        score += 25

    elif orders >= 1000:
        score += 22

    elif orders >= 500:
        score += 18

    elif orders >= 100:
        score += 14

    elif orders >= 20:
        score += 8

    elif orders > 0:
        score += 4


    # ==================================================
    # 3. TREND SIGNAL — MAX 20
    # ==================================================

    trend_score = float(
        getattr(
            product,
            "trend_score",
            0,
        )
        or 0
    )


    # Normalize a 0-100 trend score into 0-20.
    score += min(
        20,
        max(
            0,
            trend_score * 0.20,
        ),
    )


    # ==================================================
    # 4. VIDEO / DEMONSTRATION POTENTIAL — MAX 15
    # ==================================================

    has_demo_video = bool(
        getattr(
            product,
            "has_demo_video",
            False,
        )
    )

    video_potential = float(
        getattr(
            product,
            "video_potential_score",
            0,
        )
        or 0
    )


    if has_demo_video:
        score += 5


    score += min(
        10,
        max(
            0,
            video_potential * 0.10,
        ),
    )


    # ==================================================
    # 5. DATA CONFIDENCE — MAX 10
    # ==================================================

    confidence = 0


    if getattr(
        product,
        "product_url",
        None,
    ):
        confidence += 2


    if getattr(
        product,
        "image_url",
        None,
    ):
        confidence += 2


    if orders > 0:
        confidence += 2


    if float(
        getattr(
            product,
            "rating",
            0,
        )
        or 0
    ) > 0:
        confidence += 2


    if getattr(
        product,
        "supplier",
        None,
    ):
        confidence += 2


    score += confidence


    # ==================================================
    # 6. CROSS-MARKETPLACE POTENTIAL — MAX 10
    # ==================================================

    cross_status = str(
        getattr(
            product,
            "cross_marketplace_status",
            "",
        )
        or ""
    ).strip().lower()


    cross_points = {
        "matched": 10,
        "candidate_found": 7,
        "searching": 3,
        "not_checked": 0,
    }


    score += cross_points.get(
        cross_status,
        0,
    )


    return round(
        min(
            100,
            max(
                0,
                score,
            ),
        ),
        2,
    )


def get_research_intelligence_level(score):

    if score >= 75:
        return "HIGH"

    if score >= 50:
        return "MEDIUM"

    return "LOW"
