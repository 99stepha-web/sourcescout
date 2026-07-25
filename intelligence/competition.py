"""
Competition Analyzer

Evaluates how competitive a product niche is.

Higher score = Lower competition.

Author: SourceScout
"""

from __future__ import annotations

from config.intelligence import COMPETITION_CONFIG

from intelligence.analyzer import (
    AnalyzerResult,
    BaseAnalyzer,
)

from intelligence.models import IntelligenceContext


class CompetitionAnalyzer(BaseAnalyzer):

    NAME = "competition"

    def analyze(
        self,
        context: IntelligenceContext,
    ) -> AnalyzerResult:

        review_component = max(
            0.0,
            100.0 - min(context.market.review_count / 1000 * 100, 100),
        )

        follower_component = max(
            0.0,
            100.0 - min(context.supplier.follower_count / 50000 * 100, 100),
        )

        verified_component = (
            40.0 if context.supplier.verified else 100.0
        )

        rating_component = max(
            0.0,
            100.0 - (context.market.rating * 20),
        )

        weights = COMPETITION_CONFIG["weights"]

        score = (
            review_component * weights["reviews"]
            + follower_component * weights["followers"]
            + verified_component * weights["verified"]
            + rating_component * weights["rating"]
        )

        return self.result(
            score=score,
            summary="Competition evaluated from reviews, followers, supplier verification and rating.",
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
