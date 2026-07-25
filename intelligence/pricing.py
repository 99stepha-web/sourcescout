"""
Pricing Analyzer

Evaluates pricing attractiveness and cost structure.

Higher score = Better pricing opportunity.

Author: SourceScout
"""

from __future__ import annotations

from config.intelligence import PRICING_CONFIG

from intelligence.analyzer import (
    AnalyzerResult,
    BaseAnalyzer,
)
from intelligence.models import IntelligenceContext


class PricingAnalyzer(BaseAnalyzer):

    NAME = "pricing"

    def analyze(
        self,
        context: IntelligenceContext,
    ) -> AnalyzerResult:

        pricing = context.pricing

        margin_component = min(
            pricing.estimated_margin * 2,
            100.0,
        )

        shipping_component = max(
            0.0,
            100.0 - (pricing.shipping_cost * 2),
        )

        import_component = max(
            0.0,
            100.0 - pricing.estimated_import_cost,
        )

        fee_component = max(
            0.0,
            100.0 - (pricing.marketplace_fee * 5),
        )

        weights = PRICING_CONFIG["weights"]

        score = (
            margin_component * weights["margin"]
            + shipping_component * weights["shipping"]
            + import_component * weights["import"]
            + fee_component * weights["fees"]
        )

        return self.result(
            score=score,
            summary="Pricing evaluated from margin, shipping, import costs and marketplace fees.",
            details={
                "marketplace": context.marketplace,
                "estimated_margin": pricing.estimated_margin,
                "shipping_cost": pricing.shipping_cost,
                "estimated_import_cost": pricing.estimated_import_cost,
                "marketplace_fee": pricing.marketplace_fee,
                "margin_component": round(margin_component, 2),
                "shipping_component": round(shipping_component, 2),
                "import_component": round(import_component, 2),
                "fee_component": round(fee_component, 2),
            },
        )
