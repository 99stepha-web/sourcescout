"""
Profitability Analyzer

Evaluates ROI, profit margin and cost efficiency.

Higher score = Better profitability.

Author: SourceScout
"""

from __future__ import annotations

from config.intelligence import PROFITABILITY_CONFIG

from intelligence.analyzer import (
    AnalyzerResult,
    BaseAnalyzer,
)

from intelligence.models import IntelligenceContext


class ProfitabilityAnalyzer(BaseAnalyzer):

    NAME = "profitability"

    def analyze(
        self,
        context: IntelligenceContext,
    ) -> AnalyzerResult:

        pricing = context.pricing

        total_cost = (
            pricing.shipping_cost
            + pricing.estimated_import_cost
            + pricing.marketplace_fee
        )

        if total_cost > 0:
            roi = (
                pricing.estimated_margin
                / total_cost
            ) * 100
        else:
            roi = 100.0

        roi_component = min(roi, 100.0)

        margin_component = min(
            pricing.estimated_margin * 2,
            100.0,
        )

        cost_efficiency = max(
            0.0,
            100.0 - total_cost,
        )

        weights = PROFITABILITY_CONFIG["weights"]

        score = (
            roi_component * weights["roi"]
            + margin_component * weights["margin"]
            + cost_efficiency * weights["efficiency"]
        )

        return self.result(
            score=score,
            summary="Profitability evaluated from ROI, margin and operating costs.",
            details={
                "marketplace": context.marketplace,
                "roi": round(roi, 2),
                "estimated_margin": pricing.estimated_margin,
                "cost_efficiency": round(cost_efficiency, 2),
                "roi_component": round(roi_component, 2),
                "margin_component": round(margin_component, 2),
            },
        )
