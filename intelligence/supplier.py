"""
SourceScout Supplier Analyzer

Evaluates supplier quality and reliability.

Higher score = Better supplier.

Author: SourceScout
"""

from __future__ import annotations

from intelligence.analyzer import BaseAnalyzer
from intelligence.models import IntelligenceContext


class SupplierAnalyzer(BaseAnalyzer):
    """
    Evaluates supplier reliability.

    Higher score means a stronger and more trustworthy supplier.
    """

    NAME = "Supplier Analyzer"

    RATING_WEIGHT = 0.40
    YEARS_WEIGHT = 0.30
    VERIFIED_WEIGHT = 0.20
    FOLLOWER_WEIGHT = 0.10

    MAX_YEARS = 20
    MAX_FOLLOWERS = 100000

    def analyze(self, context: IntelligenceContext):

        rating_component = self._rating_component(
            context.supplier.seller_rating
        )

        years_component = self._years_component(
            context.supplier.seller_years
        )

        verified_component = self._verified_component(
            context.supplier.verified
        )

        follower_component = self._follower_component(
            context.supplier.follower_count
        )

        supplier_score = (
            rating_component * self.RATING_WEIGHT
            + years_component * self.YEARS_WEIGHT
            + verified_component * self.VERIFIED_WEIGHT
            + follower_component * self.FOLLOWER_WEIGHT
        )

        return self.result(
            score=supplier_score,
            summary=self._summary(supplier_score),
            details={
                "marketplace": context.marketplace,
                "seller_name": context.supplier.seller_name,
                "seller_rating": context.supplier.seller_rating,
                "seller_years": context.supplier.seller_years,
                "seller_followers": context.supplier.follower_count,
                "verified_supplier": context.supplier.verified,
                "rating_component": round(rating_component, 2),
                "years_component": round(years_component, 2),
                "verified_component": round(verified_component, 2),
                "follower_component": round(follower_component, 2),
            },
        )

    def _rating_component(self, rating: float) -> float:
        normalized = min(max(rating, 0.0) / 5.0, 1.0)
        return normalized * 100

    def _years_component(self, years: int) -> float:
        normalized = min(max(years, 0) / self.MAX_YEARS, 1.0)
        return normalized * 100

    @staticmethod
    def _verified_component(is_verified: bool) -> float:
        return 100.0 if is_verified else 50.0

    def _follower_component(self, followers: int) -> float:
        normalized = min(max(followers, 0) / self.MAX_FOLLOWERS, 1.0)
        return normalized * 100

    @staticmethod
    def _summary(score: float) -> str:
        if score >= 90:
            return "Excellent supplier with outstanding reliability."

        if score >= 75:
            return "Reliable supplier with a strong track record."

        if score >= 60:
            return "Generally reliable supplier."

        if score >= 40:
            return "Supplier has moderate reliability."

        return "Supplier reliability appears weak."
