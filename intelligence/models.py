"""
SourceScout Intelligence Data Models

Canonical models used by the Product Intelligence Engine.

Marketplace connectors convert raw marketplace data into these
models before analysis.

Author: SourceScout
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------
# Product Information
# ---------------------------------------------------------

@dataclass(slots=True)
class ProductMetrics:
    """
    Core product information.
    """

    product_id: str = ""

    title: str = ""

    category: str = ""

    brand: str = ""

    price: float = 0.0

    original_price: float | None = None

    currency: str = "USD"


# ---------------------------------------------------------
# Market Information
# ---------------------------------------------------------

@dataclass(slots=True)
class MarketMetrics:
    """
    Marketplace demand metrics.
    """

    monthly_sales: int = 0

    review_count: int = 0

    rating: float = 0.0

    wishlist_count: int = 0

    view_count: int = 0


# ---------------------------------------------------------
# Supplier Information
# ---------------------------------------------------------

@dataclass(slots=True)
class SupplierMetrics:
    """
    Seller reliability.
    """

    seller_id: str = ""

    seller_name: str = ""

    seller_rating: float = 0.0

    seller_years: int = 0

    follower_count: int = 0

    verified: bool = False


# ---------------------------------------------------------
# Pricing Information
# ---------------------------------------------------------

@dataclass(slots=True)
class PricingMetrics:
    """
    Commercial information.
    """

    shipping_cost: float = 0.0

    estimated_import_cost: float = 0.0

    estimated_margin: float = 0.0

    marketplace_fee: float = 0.0


# ---------------------------------------------------------
# Complete Intelligence Context
# ---------------------------------------------------------

@dataclass(slots=True)
class IntelligenceContext:
    """
    Complete normalized product information.

    Every analyzer receives this object.
    """

    marketplace: str

    product: ProductMetrics

    market: MarketMetrics

    supplier: SupplierMetrics

    pricing: PricingMetrics

    metadata: dict[str, Any] = field(default_factory=dict)
