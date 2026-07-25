"""
SourceScout Product Scorer

Aggregates analyzer results into a final intelligence score.

Author: SourceScout
"""

from __future__ import annotations

from dataclasses import dataclass

from intelligence.analyzer import AnalyzerResult
from intelligence.report import AnalyzerResults


@dataclass(slots=True)
class ScoreResult:
    """
    Final aggregated score.
    """

    overall_score: float

    decision: str

    confidence: float


class ProductScorer:
    """
    Aggregates analyzer results.

    This class contains no marketplace-specific logic.
    """

    TREND_WEIGHT = 0.30
    COMPETITION_WEIGHT = 0.20
    SUPPLIER_WEIGHT = 0.20
    PRICING_WEIGHT = 0.15
    PROFITABILITY_WEIGHT = 0.15

    def score(
        self,
        results: AnalyzerResults,
    ) -> ScoreResult:

        overall = (
            results.trend.score * self.TREND_WEIGHT
            + results.competition.score * self.COMPETITION_WEIGHT
            + results.supplier.score * self.SUPPLIER_WEIGHT
            + results.pricing.score * self.PRICING_WEIGHT
            + results.profitability.score * self.PROFITABILITY_WEIGHT
        )

        confidence = self._confidence(results)

        decision = self._decision(overall)

        return ScoreResult(
            overall_score=round(overall, 2),
            decision=decision,
            confidence=round(confidence, 2),
        )

    @staticmethod
    def _confidence(results: AnalyzerResults) -> float:
        """
        Average confidence across all analyzers.
        """

        confidences = [
            results.trend.confidence,
            results.competition.confidence,
            results.supplier.confidence,
            results.pricing.confidence,
            results.profitability.confidence,
        ]

        return sum(confidences) / len(confidences)

    @staticmethod
    def _decision(score: float) -> str:
        """
        Translate overall score into a recommendation.
        """

        if score >= 85:
            return "STRONG_BUY"

        if score >= 70:
            return "BUY"

        if score >= 55:
            return "REVIEW"

        return "REJECT"
