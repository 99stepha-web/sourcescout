"""
SourceScout Content Opportunity Scoring V1.

This score estimates whether a product is worth creating
affiliate/editorial content about.

It does NOT replace the commercial opportunity_score.

Maximum score: 100
"""


def clean_text(value):
    return str(
        value or ""
    ).strip().lower()


def calculate_content_opportunity_score(product):
    """
    SourceScout Content Opportunity Score V2.

    Comparison only.
    Does NOT modify the database.

    Maximum before penalty: 100

    Factors:
    - Proven audience demand: 25
    - Buyer / research intent: 20
    - Content expansion potential: 20
    - Social / visual potential: 15
    - Evergreen potential: 10
    - Data / content confidence: 10

    Possible title-quality penalty: up to -15
    """

    title = clean_text(
        product.title
    )

    category = clean_text(
        product.category
    )

    text = (
        title
        + " "
        + category
    )

    orders = int(
        product.orders
        or 0
    )

    rating = float(
        product.rating
        or 0
    )

    review_count = int(
        product.review_count
        or 0
    )

    score = 0.0


    # ==================================================
    # 1. PROVEN AUDIENCE DEMAND — MAX 25
    # ==================================================

    if orders >= 5000:
        demand_points = 25

    elif orders >= 1000:
        demand_points = 22

    elif orders >= 500:
        demand_points = 18

    elif orders >= 100:
        demand_points = 14

    elif orders >= 20:
        demand_points = 8

    elif orders > 0:
        demand_points = 4

    else:
        demand_points = 0


    score += demand_points


    # ==================================================
    # 2. BUYER / RESEARCH INTENT — MAX 20
    #
    # Count dimensions, not every matching keyword.
    # ==================================================

    technical_terms = (
        "solar",
        "generator",
        "power station",
        "battery",
        "inverter",
        "projector",
        "camera",
        "machine",
        "equipment",
        "printer",
        "charger",
        "electric",
        "smart",
    )

    specification_terms = (
        "w",
        "kw",
        "wh",
        "kwh",
        "mah",
        "capacity",
        "output",
        "input",
        "voltage",
        "portable",
        "automatic",
        "commercial",
    )

    lifestyle_terms = (
        "fashion",
        "jacket",
        "bag",
        "shoulder",
        "beauty",
        "fitness",
        "travel",
        "outdoor",
        "home",
        "kitchen",
        "streetwear",
    )


    has_technical_intent = any(
        term in text
        for term in technical_terms
    )

    has_specification_intent = any(
        term in text
        for term in specification_terms
    )

    has_lifestyle_intent = any(
        term in text
        for term in lifestyle_terms
    )


    if (
        has_technical_intent
        and has_specification_intent
    ):
        research_points = 20

    elif has_technical_intent:
        research_points = 17

    elif has_lifestyle_intent:
        research_points = 15

    else:
        research_points = 8


    score += research_points


    # ==================================================
    # 3. CONTENT EXPANSION POTENTIAL — MAX 20
    #
    # Estimate whether the product can support multiple
    # useful editorial formats.
    # ==================================================

    content_formats = 0


    # Review potential
    if (
        has_technical_intent
        or has_lifestyle_intent
    ):
        content_formats += 1


    # Comparison potential
    comparison_terms = (
        "projector",
        "generator",
        "power station",
        "machine",
        "equipment",
        "jacket",
        "bag",
        "camera",
        "battery",
        "solar",
    )

    if any(
        term in text
        for term in comparison_terms
    ):
        content_formats += 1


    # Buying-guide potential
    buying_guide_terms = (
        "portable",
        "smart",
        "automatic",
        "commercial",
        "fashion",
        "streetwear",
        "travel",
        "outdoor",
        "home",
    )

    if any(
        term in text
        for term in buying_guide_terms
    ):
        content_formats += 1


    # Educational / how-to potential
    educational_terms = (
        "machine",
        "equipment",
        "solar",
        "generator",
        "power station",
        "battery",
        "automatic",
        "commercial",
    )

    if any(
        term in text
        for term in educational_terms
    ):
        content_formats += 1


    if content_formats >= 4:
        expansion_points = 20

    elif content_formats == 3:
        expansion_points = 17

    elif content_formats == 2:
        expansion_points = 13

    elif content_formats == 1:
        expansion_points = 8

    else:
        expansion_points = 4


    score += expansion_points


    # ==================================================
    # 4. SOCIAL / VISUAL POTENTIAL — MAX 15
    # ==================================================

    high_visual_terms = (
        "fashion",
        "jacket",
        "bag",
        "streetwear",
        "beauty",
        "decor",
        "projector",
        "mini",
    )

    medium_visual_terms = (
        "portable",
        "smart",
        "travel",
        "outdoor",
        "fitness",
        "kitchen",
        "home",
        "camera",
    )


    if any(
        term in text
        for term in high_visual_terms
    ):
        visual_points = 15

    elif any(
        term in text
        for term in medium_visual_terms
    ):
        visual_points = 11

    elif has_technical_intent:
        visual_points = 7

    else:
        visual_points = 5


    score += visual_points


    # ==================================================
    # 5. EVERGREEN POTENTIAL — MAX 10
    # ==================================================

    seasonal_terms = (
        "christmas",
        "halloween",
        "valentine",
        "limited edition",
        "2024",
        "2025",
        "2026",
    )


    if any(
        term in text
        for term in seasonal_terms
    ):
        evergreen_points = 4

    else:
        evergreen_points = 10


    score += evergreen_points


    # ==================================================
    # 6. DATA / CONTENT CONFIDENCE — MAX 10
    # ==================================================

    confidence_points = 0


    if orders >= 100:
        confidence_points += 4

    elif orders > 0:
        confidence_points += 2


    if rating >= 4.5:
        confidence_points += 3

    elif rating >= 4.0:
        confidence_points += 2


    if review_count >= 20:
        confidence_points += 3

    elif review_count > 0:
        confidence_points += 1


    score += min(
        confidence_points,
        10,
    )


    # ==================================================
    # TITLE QUALITY PENALTY — MAX -15
    #
    # Long marketplace titles often contain duplicated
    # search terms and should not receive an advantage
    # simply because more keywords are present.
    # ==================================================

    words = title.split()

    title_penalty = 0


    if len(words) >= 30:
        title_penalty += 15

    elif len(words) >= 22:
        title_penalty += 10

    elif len(words) >= 16:
        title_penalty += 5


    # Repeated commercial keyword penalty.
    repeated_keyword_groups = (
        "solar",
        "generator",
        "power",
        "portable",
        "station",
    )

    repeated_terms = sum(
        1
        for term in repeated_keyword_groups
        if title.count(term) >= 2
    )


    if repeated_terms >= 3:
        title_penalty += 5


    title_penalty = min(
        title_penalty,
        15,
    )


    final_score = max(
        0,
        min(
            100,
            score - title_penalty,
        ),
    )


    return round(
        final_score,
        2,
    )



def get_content_opportunity_level(score):

    if score >= 80:
        return "HIGH"

    if score >= 60:
        return "MEDIUM"

    return "LOW"


def calculate_combined_priority_score(
    opportunity_score,
    content_opportunity_score,
):
    """
    SourceScout Combined Priority V2.

    Product Opportunity: 65%
    Content Opportunity: 35%
    """

    opportunity_score = float(
        opportunity_score
        or 0
    )

    content_opportunity_score = float(
        content_opportunity_score
        or 0
    )

    return round(
        (
            opportunity_score
            * 0.65
        )
        +
        (
            content_opportunity_score
            * 0.35
        ),
        2,
    )
