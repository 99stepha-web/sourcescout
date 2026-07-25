"""
SourceScout Pricing Analyzer

Evaluates commercial viability based on pricing,
shipping costs, fees, and estimated margin.

Higher score = Better commercial opportunity.

Author: SourceScout
"""

from __future__ import annotations

from intelligence.analyzer import BaseAnalyzer
from intelligence.models import IntelligenceContext


class PricingAnalyzer(BaseAnalyzer):
    """
    Evaluates pricing quality.

    Higher score indicates stronger commercial potential.
    """

    NAME = "Pricing Analyzer"

    MARGIN_WEIGHT = 0.50
    SHIPPING_WEIGHT = 0.25
    IMPORT_WEIGHT = 0.15
    FEE_WEIGHT = 0.10

    MAX_MARGIN = 100.0
    MAX_SHIPPING_COST = 50.0
    MAX_IMPORT_COST = 100.0
    MAX_MARKETPLACE_FEE = 30.0

    def analyze(self, context: IntelligenceContext):

        margin_component = self._margin_component(
            context.pricing.estimated_margin
        )

        shipping_component = self._cost_component(
            context.pricing.shipping_cost,
            self.MAX_SHIPPING_COST,
        )

        import_component = self._cost_component(
            context.pricing.estimated_import_cost,
            self.MAX_IMPORT_COST,
        )

        fee_component = self._cost_component(
            context.pricing.marketplace_fee,
            self.MAX_MARKETPLACE_FEE,
        )

        pricing_score = (
            margin_component * self.MARGIN_WEIGHT
            + shipping_component * self.SHIPPING_WEIGHT
            + import_component * self.IMPORT_WEIGHT
            + fee_component * self.FEE_WEIGHT
        )

        return self.result(
            score=pricing_score,
            summary=self._summary(pricing_score),
            details={
                "marketplace": context.marketplace,
                "estimated_margin": context.pricing.estimated_margin,
                "shipping_cost": context.pricing.shipping_cost,
                "estimated_import_cost": context.pricing.estimated_import_cost,
                "marketplace_fee": context.pricing.marketplace_fee,
                "margin_component": round(margin_component, 2),
                "shipping_component": round(shipping_component, 2),
                "import_component": round(import_component, 2),
                "fee_component": round(fee_component, 2),
            },
        )

    def _margin_component(self, margin: float) -> float:
        normalized = min(max(margin, 0.0) / self.MAX_MARGIN, 1.0)
        return normalized * 100

    @staticmethod
    def _cost_score(cost: float, maximum: float) -> float:
        normalized = min(max(cost, 0.0) / maximum, 1.0)
        return (1.0 - normalized) * 100

    def _cost_component(self, cost: float, maximum: float) -> float:
        return self._cost_score(cost, maximum)

    @staticmethod
    def _summary(score: float) -> str:
        if score >= 90:
            return "Excellent commercial pricing opportunity."

        if score >= 75:
            return "Strong pricing and healthy margins."

        if score >= 60:
            return "Commercially attractive product."

        if score >= 40:
            return "Average pricing with moderate profitability."

        return "Weak commercial pricing."
