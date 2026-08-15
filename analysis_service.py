from datetime import datetime

from claude_agent import analyze_product
from config.intelligence import SELECTION_CONFIG


def _apply_score_decision_guardrail(ai_score, decision):
    """
    Defense-in-depth: Claude returns both a numeric score and a
    decision label in one response, and they can disagree (e.g. a
    PROMOTE with a 40 score). Only ever downgrades — never promotes
    a REVIEW/SKIP upward — since Claude's qualitative reasoning for a
    conservative call may reflect risks a single number can't capture.
    """

    thresholds = SELECTION_CONFIG["approval_thresholds"]

    if ai_score is None or decision != "PROMOTE":
        return decision

    if ai_score >= thresholds["min_ai_score_for_promote"]:
        return decision

    if ai_score >= thresholds["min_ai_score_for_review"]:
        return "REVIEW"

    return "SKIP"


def analyze_and_save_product(db, product):
    """
    Analyze one product with Claude and save the
    result permanently into SQLite.
    """

    result = analyze_product(product)

    analysis = result["analysis"]
    usage = result["usage"]

    ai_score = analysis.get("ai_score")
    decision = analysis.get("decision")

    product.ai_score = ai_score
    product.ai_decision = _apply_score_decision_guardrail(ai_score, decision)

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