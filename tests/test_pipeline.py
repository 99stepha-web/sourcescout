from connectors.models import MarketplaceProduct
from intelligence.engine import IntelligenceEngine
from normalizers.alibaba import AlibabaNormalizer


def test_end_to_end_pipeline():
    product = MarketplaceProduct(
        marketplace="alibaba",
        raw_data={
            "product_id": "A1001",
            "product_title": "Wireless Earbuds",
            "category": "Electronics",
            "brand": "OEM",
            "price": 15.99,
            "original_price": 19.99,
            "currency": "USD",

            "monthly_sales": 8500,
            "review_count": 3200,
            "rating": 4.8,
            "wishlist_count": 1800,
            "view_count": 25000,

            "seller_id": "S001",
            "seller_name": "Shenzhen Factory",
            "seller_rating": 4.9,
            "seller_years": 9,
            "seller_followers": 52000,
            "verified_supplier": True,

            "shipping_cost": 3.5,
            "estimated_import_cost": 5.0,
            "estimated_margin": 38.5,
            "marketplace_fee": 2.5,

            "country": "China",
        },
    )

    context = AlibabaNormalizer().normalize(product)
    report = IntelligenceEngine().run(context)

    assert report.marketplace == "alibaba"
    assert report.product_id == "A1001"
    assert report.product_title == "Wireless Earbuds"
    assert report.overall_score > 0
    assert report.overall_decision is not None
    assert report.analyzers is not None
