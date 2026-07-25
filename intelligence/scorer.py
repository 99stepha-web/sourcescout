"""
SourceScout Product Intelligence Scoring Engine

This module converts raw marketplace product metrics into normalized
scores that can be consumed by the AI pipeline.

Every score ranges from 0-100.

The overall score is a weighted average.

Author: SourceScout
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------
# Product Metrics
# ---------------------------------------------------------

@dataclass
class ProductMetrics:
    """
    Raw marketplace metrics collected from Alibaba/Taobao.
    """

    monthly_sales: int = 0
    rating: float = 0.0
    review_count: int = 0
    seller_rating: float = 0.0
    seller_years: int = 0
    price: float = 0.0
    original_price: Optional[float] = None


# ---------------------------------------------------------
# Score Result
# ---------------------------------------------------------

@dataclass
class ScoreResult:
    trend_score: float
    competition_score: float
    supplier_score: float
    pricing_score: float
    profitability_score: float
    overall_score: float


# ---------------------------------------------------------
# Product Scorer
# ---------------------------------------------------------

class ProductScorer:

    def __init__(
        self,
        trend_weight: float = 0.25,
        competition_weight: float = 0.20,
        supplier_weight: float = 0.20,
        pricing_weight: float = 0.15,
        profitability_weight: float = 0.20,
    ):

        total = (
            trend_weight
            + competition_weight
            + supplier_weight
            + pricing_weight
            + profitability_weight
        )

        if abs(total - 1.0) > 0.0001:
            raise ValueError("Weights must total 1.0")

        self.trend_weight = trend_weight
        self.competition_weight = competition_weight
        self.supplier_weight = supplier_weight
        self.pricing_weight = pricing_weight
        self.profitability_weight = profitability_weight

    # -------------------------------------------------

    def score(self, metrics: ProductMetrics) -> ScoreResult:

        trend = self._trend(metrics)

        competition = self._competition(metrics)

        supplier = self._supplier(metrics)

        pricing = self._pricing(metrics)

        profitability = self._profitability(metrics)

        overall = (
            trend * self.trend_weight
            + competition * self.competition_weight
            + supplier * self.supplier_weight
            + pricing * self.pricing_weight
            + profitability * self.profitability_weight
        )

        return ScoreResult(
            trend_score=round(trend, 2),
            competition_score=round(competition, 2),
            supplier_score=round(supplier, 2),
            pricing_score=round(pricing, 2),
            profitability_score=round(profitability, 2),
            overall_score=round(overall, 2),
        )

    # -------------------------------------------------
    # Individual Scores
    # -------------------------------------------------

    def _trend(self, m: ProductMetrics) -> float:
        """
        Sales + reviews indicate demand.
        """

        sales = min(m.monthly_sales / 10000, 1.0)

        reviews = min(m.review_count / 3000, 1.0)

        score = (sales * 0.70 + reviews * 0.30) * 100

        return score

    # -------------------------------------------------

    def _competition(self, m: ProductMetrics) -> float:
        """
        Higher review count generally means stronger competition.

        Fewer reviews receive a higher score.
        """

        review_factor = min(m.review_count / 5000, 1.0)

        return (1.0 - review_factor) * 100

    # -------------------------------------------------

    def _supplier(self, m: ProductMetrics) -> float:
        """
        Seller reputation.
        """

        rating = min(m.seller_rating / 5.0, 1.0)

        years = min(m.seller_years / 10, 1.0)

        return (rating * 0.70 + years * 0.30) * 100

    # -------------------------------------------------

    def _pricing(self, m: ProductMetrics) -> float:
        """
        Discount percentage.

        Larger discount often improves attractiveness.
        """

        if (
            m.original_price is None
            or m.original_price <= 0
            or m.original_price <= m.price
        ):
            return 50.0

        discount = (m.original_price - m.price) / m.original_price

        return min(discount * 150, 100)

    # -------------------------------------------------

    def _profitability(self, m: ProductMetrics) -> float:
        """
        Placeholder profitability estimate.

        Will later use shipping, taxes,
        marketplace fees and advertising costs.
        """

        if m.price <= 0:
            return 0

        if m.price < 5:
            return 35

        if m.price < 15:
            return 60

        if m.price < 40:
            return 80

        return 95
