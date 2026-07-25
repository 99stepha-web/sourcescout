"""
Trend Analyzer

Evaluates product demand based on market sales and reviews.

Author: SourceScout
"""

from __future__ import annotations

from config.intelligence import TREND_CONFIG

from intelligence.analyzer import (
    AnalyzerResult,
    BaseAnalyzer,
)
from intelligence.models import IntelligenceContext


class TrendAnalyzer(BaseAnalyzer):
    """
    Analyze overall market demand.
    """

    NAME = "trend"

    @staticmethod
    def _band_score(value: int, bands: list[tuple[int, int]]) -> float:
        """
        Convert a raw value into a calibrated score.
        """
        for limit, score in bands:
            if value <= limit:
                return float(score)

        return 100.0

    def analyze(
        self,
        context: IntelligenceContext,
    ) -> AnalyzerResult:

        sales_score = self._band_score(
            context.market.monthly_sales,
            TREND_CONFIG["sales_bands"],
        )

        review_score = self._band_score(
            context.market.review_count,
            TREND_CONFIG["review_bands"],
        )

        weights = TREND_CONFIG["weights"]

        score = (
            sales_score * weights["sales"]
            + review_score * weights["reviews"]
        )

        return self.result(
            score=score,
            summary="Market demand evaluated from sales and reviews.",
            details={
                "marketplace": context.marketplace,
                "monthly_sales": context.market.monthly_sales,
                "review_count": context.market.review_count,
                "sales_score": sales_score,
                "review_score": review_score,
            },
        )
