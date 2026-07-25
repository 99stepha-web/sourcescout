"""
SourceScout Intelligence Analyzer Framework

Defines the common interface and shared utilities used by all
Product Intelligence analyzers.

Every analyzer returns a standardized AnalyzerResult object.

Author: SourceScout
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict


# ---------------------------------------------------------
# Standard Analyzer Result
# ---------------------------------------------------------

@dataclass(slots=True)
class AnalyzerResult:
    """
    Standard output returned by every analyzer.
    """

    score: float
    level: str
    confidence: float
    summary: str
    details: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------
# Base Analyzer
# ---------------------------------------------------------

class BaseAnalyzer(ABC):
    """
    Base class for all SourceScout intelligence analyzers.

    Every analyzer must implement analyze().
    """

    NAME = "Base Analyzer"

    @abstractmethod
    def analyze(self, metrics) -> AnalyzerResult:
        """
        Analyze product metrics.

        Returns
        -------
        AnalyzerResult
        """
        raise NotImplementedError

    # -------------------------------------------------

    @staticmethod
    def clamp(score: float) -> float:
        """
        Restrict a score to 0-100.
        """
        return max(0.0, min(100.0, score))

    # -------------------------------------------------

    @staticmethod
    def level(score: float) -> str:

        if score >= 90:
            return "EXCELLENT"

        if score >= 75:
            return "GOOD"

        if score >= 60:
            return "FAIR"

        if score >= 40:
            return "WEAK"

        return "POOR"

    # -------------------------------------------------

    @staticmethod
    def confidence(score: float) -> float:
        """
        Initial confidence estimate.

        This will become more sophisticated later.
        """

        return round(BaseAnalyzer.clamp(score) / 100.0, 2)

    # -------------------------------------------------

    def result(
        self,
        score: float,
        summary: str,
        details: Dict[str, Any] | None = None,
    ) -> AnalyzerResult:

        score = self.clamp(score)

        return AnalyzerResult(
            score=round(score, 2),
            level=self.level(score),
            confidence=self.confidence(score),
            summary=summary,
            details=details or {},
        )
