"""
Alibaba Marketplace Normalizer.

Converts a MarketplaceProduct into the canonical
IntelligenceContext used by the Intelligence Engine.

Author: SourceScout
"""

from __future__ import annotations

from connectors.models import MarketplaceProduct

from intelligence.models import (
    IntelligenceContext,
    MarketMetrics,
    PricingMetrics,
    ProductMetrics,
    SupplierMetrics,
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

            product=ProductMetrics(
                product_id=raw["product_id"],
                title=raw["product_title"],
                category=raw.get("category", ""),
                brand=raw.get("brand", ""),
                price=raw.get("price", 0.0),
                original_price=raw.get("original_price"),
                currency=raw.get("currency", "USD"),
            ),

            market=MarketMetrics(
                monthly_sales=raw["monthly_sales"],
                review_count=raw["review_count"],
                rating=raw["rating"],
                wishlist_count=raw.get("wishlist_count", 0),
                view_count=raw.get("view_count", 0),
            ),

            supplier=SupplierMetrics(
                seller_id=raw.get("seller_id", ""),
                seller_name=raw["seller_name"],
                seller_rating=raw["seller_rating"],
                seller_years=raw["seller_years"],
                follower_count=raw["seller_followers"],
                verified=raw["verified_supplier"],
            ),

            pricing=PricingMetrics(
                shipping_cost=raw["shipping_cost"],
                estimated_import_cost=raw["estimated_import_cost"],
                estimated_margin=raw["estimated_margin"],
                marketplace_fee=raw["marketplace_fee"],
            ),

            metadata={
                "source": "alibaba",
                "country": raw.get("country", "China"),
            },
        )
