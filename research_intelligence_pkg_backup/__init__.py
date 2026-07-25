"""
SourceScout Research Intelligence Engine

This package calculates all research intelligence metrics for products.

Modules:
- competition
- video
- keyword
- evergreen
- seasonality
- trend
- cross_market
"""

from .engine import calculate_research_intelligence

__all__ = ["calculate_research_intelligence"]
