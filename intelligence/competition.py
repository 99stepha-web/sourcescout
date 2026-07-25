"""
SourceScout Competition Analyzer

Evaluates market saturation using normalized intelligence models.

Higher score = Lower competition.

Author: SourceScout
"""

from __future__ import annotations

from intelligence.analyzer import BaseAnalyzer
from intelligence.models import IntelligenceContext


class CompetitionAnalyzer(BaseAnalyzer):
    """
    Evaluates market competition.

    Higher score means lower competition.
    """

    NAME = "Competition Analyzer"

    REVIEW_WEIGHT = 0.40
    FOLLOWER_WEIGHT = 0.30
    VERIFIED_WEIGHT = 0.20
    RATING_WEIGHT = 0.10

    MAX_REVIEWS = 5000
    MAX_FOLLOWERS = 100000

    def analyze(self, context: IntelligenceContext):

        review_component = self._review_component(
            context.market.review_count
        )

        follower_component = self._follower_component(
            context.supplier.follower_count
        )

        verified_component = self._verified_component(
            context.supplier.verified
        )

        rating_component = self._rating_component(
            context.market.rating
        )

        competition_score = (
            review_component * self.REVIEW_WEIGHT
            + follower_component * self.FOLLOWER_WEIGHT
            + verified_component * self.VERIFIED_WEIGHT
            + rating_component * self.RATING_WEIGHT
        )

        return self.result(
            score=competition_score,
            summary=self._summary(competition_score),
            details={
                "marketplace": context.marketplace,
                "review_count": context.market.review_count,
                "seller_followers": context.supplier.follower_count,
                "verified_supplier": context.supplier.verified,
                "rating": context.market.rating,
                "review_component": round(review_component, 2),
                "follower_component": round(follower_component, 2),
                "verified_component": round(verified_component, 2),
                "rating_component": round(rating_component, 2),
            },
        )

    # -------------------------------------------------

    def _review_component(self, reviews: int) -> float:
        """
        More reviews generally indicate stronger competition.
        """
        normalized = min(reviews / self.MAX_REVIEWS, 1.0)
        return (1.0 - normalized) * 100

    # -------------------------------------------------

    def _follower_component(self, followers: int) -> float:
        """
        Large seller audiences increase competition.
        """
        normalized = min(followers / self.MAX_FOLLOWERS, 1.0)
        return (1.0 - normalized) * 100

    # -------------------------------------------------

    @staticmethod
    def _verified_component(is_verified: bool) -> float:
        """
        Verified suppliers usually make the market more competitive.
        """
        return 40.0 if is_verified else 100.0

    # -------------------------------------------------

    @staticmethod
    def _rating_component(rating: float) -> float:
        """
        Higher ratings suggest stronger competitors.
        """
        normalized = min(rating / 5.0, 1.0)
        return (1.0 - normalized) * 100

    # -------------------------------------------------

    @staticmethod
    def _summary(score: float) -> str:

        if score >= 90:
            return "Very low competition with strong entry potential."

        if score >= 75:
            return "Moderate competition and attractive opportunity."

        if score >= 60:
            return "Competitive market with room to differentiate."

        if score >= 40:
            return "Highly competitive market."

        return "Extremely saturated market."
