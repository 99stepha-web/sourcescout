"""
Alibaba Marketplace Connector (Placeholder)

Author: SourceScout
"""

from __future__ import annotations

from connectors.base import BaseMarketplaceConnector
from connectors.models import MarketplaceProduct


class AlibabaConnector(BaseMarketplaceConnector):

    NAME = "Alibaba"

    def search(
        self,
        keyword: str,
        limit: int = 20,
    ) -> list[MarketplaceProduct]:

        raise NotImplementedError(
            "Alibaba search connector not implemented yet."
        )

    def product(
        self,
        product_id: str,
    ) -> MarketplaceProduct:

        raise NotImplementedError(
            "Alibaba product connector not implemented yet."
        )
