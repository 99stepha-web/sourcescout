"""
Alibaba marketplace connector.

Author: SourceScout
"""

from __future__ import annotations

from connectors.alibaba_parser import AlibabaParser
from connectors.base import BaseMarketplaceConnector
from connectors.http.fetcher import ProductFetcher
from connectors.models import MarketplaceProduct


class AlibabaConnector(BaseMarketplaceConnector):

    NAME = "Alibaba"

    def __init__(
        self,
        fetcher: ProductFetcher | None = None,
        parser: AlibabaParser | None = None,
    ) -> None:
        self._fetcher = fetcher or ProductFetcher()
        self._parser = parser or AlibabaParser()

    def search(
        self,
        keyword: str,
        limit: int = 20,
    ) -> list[MarketplaceProduct]:
        raise NotImplementedError("Alibaba search is not implemented yet.")

    def product(
        self,
        product_id: str,
    ) -> MarketplaceProduct:
        html = self._fetcher.fetch(product_id)
        return self._parser.parse(html)

    def load(
        self,
        url: str,
    ) -> MarketplaceProduct:
        return self.product(url)

    def close(self) -> None:
        self._fetcher.close()
