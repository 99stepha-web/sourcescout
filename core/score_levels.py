"""
SourceScout Score Levels

Shared score classification used by every intelligence engine.
"""


def score_to_level(score: float) -> str:
    """
    Convert a numeric score (0–100) into a standardized level.
    """

    if score >= 90:
        return "Excellent"

    if score >= 75:
        return "High"

    if score >= 60:
        return "Medium"

    if score >= 40:
        return "Low"

    return "Very Low"
