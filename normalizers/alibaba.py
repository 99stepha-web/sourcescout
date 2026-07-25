"""
Alibaba Marketplace Normalizer.

Author: SourceScout
"""

from __future__ import annotations

from connectors.models import MarketplaceProduct
from intelligence.models import (
    CompetitionData,
    IntelligenceContext,
    PricingData,
    SupplierData,
    TrendData,
)
from normalizers.base import BaseNormalizer


class AlibabaNormalizer(BaseNormalizer):

    NAME = "Alibaba"

    def normalize(
        self,
        product: MarketplaceProduct,
    ) -> IntelligenceContext:

        raw = product.raw_data

        return IntelligenceContext(
            marketplace=product.marketplace,
            product_id=raw["product_id"],
            product_title=raw["product_title"],

            trend=TrendData(
                monthly_sales=raw["monthly_sales"],
                review_count=raw["review_count"],
            ),

            competition=CompetitionData(
                review_count=raw["review_count"],
                seller_followers=raw["seller_followers"],
                verified_supplier=raw["verified_supplier"],
                rating=raw["rating"],
            ),

            supplier=SupplierData(
                seller_name=raw["seller_name"],
                seller_rating=raw["seller_rating"],
                seller_years=raw["seller_years"],
                follower_count=raw["seller_followers"],
                verified=raw["verified_supplier"],
            ),

            pricing=PricingData(
                estimated_margin=raw["estimated_margin"],
                shipping_cost=raw["shipping_cost"],
                estimated_import_cost=raw["estimated_import_cost"],
                marketplace_fee=raw["marketplace_fee"],
            ),

            metadata={
                "source": "alibaba",
                "country": raw.get("country", "China"),
            },
        )
