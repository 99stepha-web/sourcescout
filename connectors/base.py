"""
Base Marketplace Connector.

Author: SourceScout
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from connectors.models import MarketplaceProduct


class BaseMarketplaceConnector(ABC):

    NAME = "base"

    @abstractmethod
    def search(
        self,
        keyword: str,
        limit: int = 20,
    ) -> list[MarketplaceProduct]:
        raise NotImplementedError

    @abstractmethod
    def product(
        self,
        product_id: str,
    ) -> MarketplaceProduct:
        raise NotImplementedError
