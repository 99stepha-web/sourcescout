"""
SourceScout Trend Analyzer

Evaluates market demand using normalized intelligence models.

Author: SourceScout
"""

from __future__ import annotations

from intelligence.analyzer import BaseAnalyzer
from intelligence.models import IntelligenceContext


class TrendAnalyzer(BaseAnalyzer):
    """
    Measures product demand.

    Uses normalized marketplace data only.
    """

    NAME = "Trend Analyzer"

    SALES_WEIGHT = 0.70
    REVIEW_WEIGHT = 0.30

    MAX_MONTHLY_SALES = 10000
    MAX_REVIEWS = 3000

    def analyze(self, context: IntelligenceContext):

        sales_score = self._normalize(
            context.market.monthly_sales,
            self.MAX_MONTHLY_SALES,
        )

        review_score = self._normalize(
            context.market.review_count,
            self.MAX_REVIEWS,
        )

        trend_score = (
            sales_score * self.SALES_WEIGHT +
            review_score * self.REVIEW_WEIGHT
        )

        return self.result(
            score=trend_score,
            summary=self._summary(trend_score),
            details={
                "marketplace": context.marketplace,
                "monthly_sales": context.market.monthly_sales,
                "review_count": context.market.review_count,
                "sales_score": round(sales_score, 2),
                "review_score": round(review_score, 2),
            },
        )

    @staticmethod
    def _normalize(value: int, maximum: int) -> float:

        if value <= 0:
            return 0.0

        return min(value / maximum, 1.0) * 100

    @staticmethod
    def _summary(score: float) -> str:

        if score >= 90:
            return "Exceptional market demand."

        if score >= 75:
            return "Strong and growing demand."

        if score >= 60:
            return "Healthy demand."

        if score >= 40:
            return "Moderate demand."

        return "Weak demand."
