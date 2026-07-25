"""
Alibaba Marketplace Normalizer.

Author: SourceScout
"""

from __future__ import annotations

from connectors.models import MarketplaceProduct
from intelligence.models import IntelligenceContext
from normalizers.base import BaseNormalizer


class AlibabaNormalizer(BaseNormalizer):

    NAME = "Alibaba"

    def normalize(
        self,
        product: MarketplaceProduct,
    ) -> IntelligenceContext:

        raise NotImplementedError(
            "Alibaba normalizer not implemented yet."
        )
