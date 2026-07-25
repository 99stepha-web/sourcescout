"""
SourceScout Profitability Analyzer

Evaluates the overall earning potential of a product.

Higher score = Better profitability.

Author: SourceScout
"""

from __future__ import annotations

from intelligence.analyzer import BaseAnalyzer
from intelligence.models import IntelligenceContext


class ProfitabilityAnalyzer(BaseAnalyzer):
    """
    Evaluates the financial attractiveness of a product.
    """

    NAME = "Profitability Analyzer"

    ROI_WEIGHT = 0.50
    MARGIN_WEIGHT = 0.30
    COST_EFFICIENCY_WEIGHT = 0.20

    MAX_MARGIN = 100.0
    MAX_ROI = 300.0

    def analyze(self, context: IntelligenceContext):

        roi = self._calculate_roi(context)

        roi_component = self._roi_component(roi)

        margin_component = self._margin_component(
            context.pricing.estimated_margin
        )

        cost_efficiency = self._cost_efficiency(context)

        profitability_score = (
            roi_component * self.ROI_WEIGHT
            + margin_component * self.MARGIN_WEIGHT
            + cost_efficiency * self.COST_EFFICIENCY_WEIGHT
        )

        return self.result(
            score=profitability_score,
            summary=self._summary(profitability_score),
            details={
                "marketplace": context.marketplace,
                "roi": round(roi, 2),
                "estimated_margin": context.pricing.estimated_margin,
                "cost_efficiency": round(cost_efficiency, 2),
                "roi_component": round(roi_component, 2),
                "margin_component": round(margin_component, 2),
            },
        )

    def _calculate_roi(self, context: IntelligenceContext) -> float:
        total_cost = (
            context.product.price
            + context.pricing.shipping_cost
            + context.pricing.estimated_import_cost
            + context.pricing.marketplace_fee
        )

        if total_cost <= 0:
            return 0.0

        return (
            context.pricing.estimated_margin /
            total_cost
        ) * 100

    def _cost_efficiency(self, context: IntelligenceContext) -> float:
        total_cost = (
            context.pricing.shipping_cost
            + context.pricing.estimated_import_cost
            + context.pricing.marketplace_fee
        )

        if total_cost <= 0:
            return 100.0

        efficiency = (
            context.pricing.estimated_margin /
            total_cost
        ) * 100

        return min(max(efficiency, 0.0), 100.0)

    def _roi_component(self, roi: float) -> float:
        normalized = min(max(roi, 0.0) / self.MAX_ROI, 1.0)
        return normalized * 100

    def _margin_component(self, margin: float) -> float:
        normalized = min(max(margin, 0.0) / self.MAX_MARGIN, 1.0)
        return normalized * 100

    @staticmethod
    def _summary(score: float) -> str:
        if score >= 90:
            return "Outstanding profit potential."

        if score >= 75:
            return "Strong profitability."

        if score >= 60:
            return "Healthy profit opportunity."

        if score >= 40:
            return "Moderate profitability."

        return "Low profit potential."
