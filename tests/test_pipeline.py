"""
End-to-end pipeline integration test.

Author: SourceScout
"""

from __future__ import annotations

import json
from pathlib import Path

from connectors.models import MarketplaceProduct
from intelligence.engine import IntelligenceEngine
from normalizers.alibaba import AlibabaNormalizer


def test_pipeline():

    fixture = (
        Path(__file__).parent
        / "fixtures"
        / "alibaba_product.json"
    )

    raw = json.loads(fixture.read_text())

    product = MarketplaceProduct(
        marketplace="Alibaba",
        raw_data=raw,
    )

    context = AlibabaNormalizer().normalize(product)

    report = IntelligenceEngine().run(context)

    assert report.marketplace == "Alibaba"

    assert report.product_id == raw["product_id"]

    assert report.product_title == raw["product_title"]

    assert 0 <= report.overall_score <= 100

    assert report.overall_decision in {
        "REJECT",
        "REVIEW",
        "BUY",
        "STRONG_BUY",
    }

    analyzers = report.analyzers

    assert analyzers.trend is not None
    assert analyzers.competition is not None
    assert analyzers.supplier is not None
    assert analyzers.pricing is not None
    assert analyzers.profitability is not None
