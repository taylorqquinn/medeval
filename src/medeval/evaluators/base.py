"""Base evaluator interface."""

from abc import ABC, abstractmethod
from medeval.models import ClinicalCase, Prediction
from typing import Dict, Any

class Evaluator(ABC):
    """Abstract evaluator interface."""

    @abstractmethod
    def evaluate(self, case: ClinicalCase, prediction: Prediction) -> Dict[str, Any]:
        """Evaluate a single prediction and return a dict of metric names to values."""
        raise NotImplementedError
