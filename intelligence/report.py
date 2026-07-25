"""
SourceScout Intelligence Report Models

Defines the canonical output produced by the
Product Intelligence Engine.

Author: SourceScout
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any

from intelligence.analyzer import AnalyzerResult


# ---------------------------------------------------------
# Analyzer Result Collection
# ---------------------------------------------------------

@dataclass(slots=True)
class AnalyzerResults:
    """
    Collection of analyzer outputs.
    """

    trend: AnalyzerResult

    competition: AnalyzerResult

    supplier: AnalyzerResult

    pricing: AnalyzerResult

    profitability: AnalyzerResult

    def as_dict(self) -> dict[str, AnalyzerResult]:
        """
        Return analyzer results as a dictionary.
        """

        return {
            "trend": self.trend,
            "competition": self.competition,
            "supplier": self.supplier,
            "pricing": self.pricing,
            "profitability": self.profitability,
        }


# ---------------------------------------------------------
# Final Intelligence Report
# ---------------------------------------------------------

@dataclass(slots=True)
class IntelligenceReport:
    """
    Final output of the Product Intelligence Engine.
    """

    marketplace: str

    product_id: str

    product_title: str

    overall_score: float

    overall_decision: str

    analyzers: AnalyzerResults

    generated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        """
        Lightweight summary suitable for APIs,
        dashboards and AI prompts.
        """

        return {
            "marketplace": self.marketplace,
            "product_id": self.product_id,
            "product_title": self.product_title,
            "overall_score": round(self.overall_score, 2),
            "overall_decision": self.overall_decision,
            "generated_at": self.generated_at.isoformat(),
        }

    def full_report(self) -> dict[str, Any]:
        """
        Complete report including all analyzers.
        """

        return {
            **self.summary(),
            "analyzers": {
                name: {
                    "score": result.score,
                    "level": result.level,
                    "confidence": result.confidence,
                    "summary": result.summary,
                    "details": result.details,
                }
                for name, result in self.analyzers.as_dict().items()
            },
            "metadata": self.metadata,
        }
