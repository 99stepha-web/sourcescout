"""
SourceScout Base Intelligence Engine

Every intelligence engine should inherit from BaseEngine and
implement the calculate() method.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from core.engine_result import EngineResult


class BaseEngine(ABC):
    """
    Abstract base class for all SourceScout intelligence engines.
    """

    name: str = "base"

    @abstractmethod
    def calculate(self, data: Dict[str, Any]) -> EngineResult:
        """
        Calculate the engine's score.

        Args:
            data: Product or research data.

        Returns:
            EngineResult
        """
        raise NotImplementedError
