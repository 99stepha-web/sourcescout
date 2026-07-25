"""
Base Marketplace Normalizer.

Author: SourceScout
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from connectors.models import MarketplaceProduct
from intelligence.models import IntelligenceContext


class BaseNormalizer(ABC):

    NAME = "base"

    @abstractmethod
    def normalize(
        self,
        product: MarketplaceProduct,
    ) -> IntelligenceContext:
        raise NotImplementedError
