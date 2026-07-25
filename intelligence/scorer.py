"""
SourceScout Product Scorer

Aggregates analyzer results into a final product score.

Author: SourceScout
"""

from __future__ import annotations

from dataclasses import dataclass

from config.intelligence import SCORER_CONFIG

from intelligence.report import AnalyzerResults


@dataclass(slots=True)
class ScoreResult:
    overall_score: float
    decision: str
    confidence: float


class ProductScorer:

    def score(
        self,
        results: AnalyzerResults,
    ) -> ScoreResult:

        weights = SCORER_CONFIG["weights"]

        overall = (
            results.trend.score * weights["trend"]
            + results.competition.score * weights["competition"]
            + results.supplier.score * weights["supplier"]
            + results.pricing.score * weights["pricing"]
            + results.profitability.score * weights["profitability"]
        )

        confidence = (
            results.trend.confidence
            + results.competition.confidence
            + results.supplier.confidence
            + results.pricing.confidence
            + results.profitability.confidence
        ) / 5

        thresholds = SCORER_CONFIG["decision_thresholds"]

        if overall >= thresholds["STRONG_BUY"]:
            decision = "STRONG_BUY"
        elif overall >= thresholds["BUY"]:
            decision = "BUY"
        elif overall >= thresholds["REVIEW"]:
            decision = "REVIEW"
        else:
            decision = "REJECT"

        return ScoreResult(
            overall_score=round(overall, 2),
            decision=decision,
            confidence=round(confidence, 2),
        )
