"""
SourceScout End-to-End Demo Pipeline

Creates a realistic IntelligenceContext,
runs the IntelligenceEngine,
and prints the resulting report.

Author: SourceScout
"""

from __future__ import annotations

from intelligence.engine import IntelligenceEngine
from intelligence.models import (
    IntelligenceContext,
    MarketMetrics,
    PricingMetrics,
    ProductMetrics,
    SupplierMetrics,
)


def build_demo_context() -> IntelligenceContext:
    return IntelligenceContext(
        marketplace="Alibaba",
        product=ProductMetrics(
            product_id="ALI-100001",
            title="Minimalist Japanese Shoulder Bag",
            category="Women's Bags",
            brand="OEM",
            price=12.50,
            currency="USD",
        ),
        market=MarketMetrics(
            monthly_sales=4200,
            review_count=680,
            rating=4.8,
            wishlist_count=1450,
            view_count=38200,
        ),
        supplier=SupplierMetrics(
            seller_id="SUP-88",
            seller_name="Guangzhou Fashion Factory",
            seller_rating=4.9,
            seller_years=8,
            follower_count=26000,
            verified=True,
        ),
        pricing=PricingMetrics(
            shipping_cost=3.40,
            estimated_import_cost=1.10,
            estimated_margin=18.75,
            marketplace_fee=0.75,
        ),
        metadata={
            "source": "demo",
            "country": "China",
        },
    )


def main():

    context = build_demo_context()

    engine = IntelligenceEngine()

    report = engine.run(context)

    print("=" * 60)
    print("SOURCE SCOUT DEMO")
    print("=" * 60)
    print()

    print(report.summary())
    print()
    print(report.full_report())


if __name__ == "__main__":
    main()
