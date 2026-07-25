"""
Marketplace connector models.

Author: SourceScout
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class MarketplaceProduct:

    marketplace: str

    raw_data: dict[str, Any]
