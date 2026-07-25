"""
SourceScout Research Intelligence Engine

This is the central entry point for all research intelligence
calculations. Additional scorers (competition, keyword, video,
evergreen, seasonality, etc.) will be integrated here.
"""


def calculate_research_intelligence(product):
    """
    Temporary implementation.

    Returns a default research intelligence result until the
    individual scoring engines are implemented.
    """

    return {
        "research_score": 0.0,
        "research_level": "Not Calculated",
        "competition_score": 0.0,
        "competition_level": "Not Calculated",
        "video_score": 0.0,
        "video_level": "Not Calculated",
        "keyword_score": 0.0,
        "keyword_level": "Not Calculated",
        "evergreen_score": 0.0,
        "evergreen_level": "Not Calculated",
        "seasonality_score": 0.0,
        "seasonality_level": "Not Calculated",
    }
