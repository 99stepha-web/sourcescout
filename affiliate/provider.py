"""
SourceScout Affiliate Provider Interface

Every affiliate network must implement this interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class AffiliateLink:
    """
    Standard affiliate link returned by any provider.
    """

    original_url: str
    affiliate_url: str
    provider: str
    desktop_url: Optional[str] = None
    mobile_url: Optional[str] = None
    app_url: Optional[str] = None


class AffiliateProvider(ABC):
    """
    Base class for all affiliate providers.
    """

    name: str = "provider"

    @abstractmethod
    def generate_product_link(self, product_id: str) -> AffiliateLink:
        """
        Generate an affiliate link using a product ID.
        """
        raise NotImplementedError

    @abstractmethod
    def generate_url_link(self, url: str) -> AffiliateLink:
        """
        Generate an affiliate link using a product URL.
        """
        raise NotImplementedError
