from datetime import datetime

from claude_agent import analyze_product


def analyze_and_save_product(db, product):
    """
    Analyze one product with Claude and save the
    result permanently into SQLite.
    """

    result = analyze_product(product)

    analysis = result["analysis"]
    usage = result["usage"]

    product.ai_score = analysis.get("ai_score")
    product.ai_decision = analysis.get("decision")

    product.target_audience = analysis.get(
        "target_audience"
    )

    product.content_potential = analysis.get(
        "content_potential"
    )

    product.best_content_angle = analysis.get(
        "best_content_angle"
    )

    product.why_it_could_sell = analysis.get(
        "why_it_could_sell"
    )

    product.risks = analysis.get(
        "risks"
    )

    product.verification_needed = analysis.get(
        "verification_needed"
    )

    product.ai_input_tokens = usage.get(
        "input_tokens",
        0,
    )

    product.ai_output_tokens = usage.get(
        "output_tokens",
        0,
    )

    product.ai_analyzed_at = datetime.utcnow()

    product.status = "AI_ANALYZED"

    db.commit()
    db.refresh(product)

    return product