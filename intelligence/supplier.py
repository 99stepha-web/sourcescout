"""
Supplier Analyzer

Evaluates supplier reliability and credibility.

Higher score = Better supplier.

Author: SourceScout
"""

from __future__ import annotations

from config.intelligence import SUPPLIER_CONFIG

from intelligence.analyzer import (
    AnalyzerResult,
    BaseAnalyzer,
)

from intelligence.models import IntelligenceContext


class SupplierAnalyzer(BaseAnalyzer):

    NAME = "supplier"

    def analyze(
        self,
        context: IntelligenceContext,
    ) -> AnalyzerResult:

        rating_component = min(
            context.supplier.seller_rating * 20,
            100.0,
        )

        years_component = min(
            context.supplier.seller_years * 5,
            100.0,
        )

        verified_component = (
            100.0 if context.supplier.verified else 0.0
        )

        follower_component = min(
            context.supplier.follower_count / 1000,
            100.0,
        )

        weights = SUPPLIER_CONFIG["weights"]

        score = (
            rating_component * weights["rating"]
            + years_component * weights["years"]
            + verified_component * weights["verified"]
            + follower_component * weights["followers"]
        )

        return self.result(
            score=score,
            summary="Supplier reliability evaluated from rating, experience, verification and followers.",
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
