"""
SourceScout Intelligence Engine Result

Standard result object returned by every intelligence engine.
"""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class EngineResult:
    """
    Standard response returned by every intelligence engine.
    """

    engine: str
    score: float
    level: str
    signals: Dict[str, Any] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result into a serializable dictionary."""
        return {
            "engine": self.engine,
            "score": self.score,
            "level": self.level,
            "signals": self.signals,
            "details": self.details,
        }
