"""
SourceScout Intelligence Engine

Coordinates analyzers and produces the final
IntelligenceReport.

Author: SourceScout
"""

from __future__ import annotations

from intelligence.models import IntelligenceContext
from intelligence.report import (
    AnalyzerResults,
    IntelligenceReport,
)
from intelligence.scorer import ProductScorer

from intelligence.trend import TrendAnalyzer
from intelligence.competition import CompetitionAnalyzer
from intelligence.supplier import SupplierAnalyzer
from intelligence.pricing import PricingAnalyzer
from intelligence.profitability import ProfitabilityAnalyzer


class IntelligenceEngine:
    """
    Executes all analyzers and builds
    the final intelligence report.
    """

    def __init__(self, analyzers=None):

        self.analyzers = analyzers or [
            TrendAnalyzer(),
            CompetitionAnalyzer(),
            SupplierAnalyzer(),
            PricingAnalyzer(),
            ProfitabilityAnalyzer(),
        ]

        self.scorer = ProductScorer()

    def run(
        self,
        context: IntelligenceContext,
    ) -> IntelligenceReport:

        analyzer_map = {}

        for analyzer in self.analyzers:
            analyzer_map[analyzer.NAME] = analyzer.analyze(context)

        results = AnalyzerResults(
            trend=analyzer_map[TrendAnalyzer.NAME],
            competition=analyzer_map[CompetitionAnalyzer.NAME],
            supplier=analyzer_map[SupplierAnalyzer.NAME],
            pricing=analyzer_map[PricingAnalyzer.NAME],
            profitability=analyzer_map[ProfitabilityAnalyzer.NAME],
        )

        score = self.scorer.score(results)

        return IntelligenceReport(
            marketplace=context.marketplace,
            product_id=context.product.product_id,
            product_title=context.product.title,
            overall_score=score.overall_score,
            overall_decision=score.decision,
            analyzers=results,
            metadata=context.metadata,
        )
