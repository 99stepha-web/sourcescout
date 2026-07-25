"""
SourceScout Affiliate Models

Shared request and response models for affiliate providers.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PromotionRequest:
    """
    Request for generating an affiliate link.
    """

    product_id: Optional[str] = None
    product_url: Optional[str] = None


@dataclass
class PromotionResponse:
    """
    Standardized affiliate response.
    """

    provider: str

    original_url: str

    affiliate_url: str

    desktop_url: Optional[str] = None

    mobile_url: Optional[str] = None

    app_url: Optional[str] = None
