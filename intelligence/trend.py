"""
Trend Analyzer

Evaluates market demand based on sales and reviews.
"""

from __future__ import annotations

from config.intelligence import TREND_CONFIG

from intelligence.analyzer import (
    AnalyzerResult,
    BaseAnalyzer,
)

from intelligence.models import IntelligenceContext


class TrendAnalyzer(BaseAnalyzer):

    NAME = "trend"

    @staticmethod
    def _band_score(value: int, bands: list[tuple[int, int]]) -> float:
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
            confidence=score / 100,
            summary=self.level(score),
            details={
                "marketplace": context.marketplace,
                "monthly_sales": context.market.monthly_sales,
                "review_count": context.market.review_count,
                "sales_score": sales_score,
                "review_score": review_score,
            },
        )
