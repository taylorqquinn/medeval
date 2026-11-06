"""Base evaluator interface with plugin support.

This module provides the base Evaluator class that all evaluators must inherit from.
It also includes utilities for discovering and loading custom evaluators via Python
entry points, enabling a plugin system for extensibility.

Example custom evaluator package structure:
    my_custom_evaluators/
        setup.py or pyproject.toml with:
            [project.entry-points."medeval.evaluators"]
            my_evaluator = "my_package:MyEvaluator"
"""

import importlib.metadata
import logging
from abc import ABC, abstractmethod
from typing import Any

from medeval.models import ClinicalCase, Prediction

logger = logging.getLogger(__name__)


class Evaluator(ABC):
    """Abstract base class for all evaluators.

    All evaluators must inherit from this class and implement the evaluate() method.
    Custom evaluators can be registered via Python entry points to enable plugin
    functionality.

    Attributes:
        name: Optional name for the evaluator (defaults to class name)

    Example:
        class MyEvaluator(Evaluator):
            def evaluate(self, case, prediction):
                return {"my_metric": 0.95}
    """

    def __init__(self, name: str = None):
        """Initialize the evaluator.

        Args:
            name: Optional name for this evaluator instance. If not provided,
                  uses the class name.
        """
        self.name = name or self.__class__.__name__

    @abstractmethod
    def evaluate(self, case: ClinicalCase, prediction: Prediction) -> dict[str, Any]:
        """Evaluate a single prediction and return metrics.

        Args:
            case: The clinical case containing ground truth data
            prediction: The model's prediction to evaluate

        Returns:
            Dictionary mapping metric names (str) to metric values (Any).
            Metric values are typically float, int, bool, or str.

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError


def discover_evaluators() -> dict[str, type[Evaluator]]:
    """Discover all registered evaluator plugins via entry points.

    Searches for Python packages that have registered evaluators under the
    "medeval.evaluators" entry point group. This enables third-party packages
    to provide custom evaluators without modifying the medeval framework.

    Returns:
        Dictionary mapping evaluator names to Evaluator classes.
        Built-in evaluators are included by default.

    Example:
        evaluators = discover_evaluators()
        if "my_custom_evaluator" in evaluators:
            evaluator = evaluators["my_custom_evaluator"]()
    """
    discovered = {}

    # Discover plugins via entry points
    try:
        entry_points = importlib.metadata.entry_points()

        # Handle both old and new entry_points() API
        if hasattr(entry_points, "select"):
            # Python 3.10+ API
            medeval_eps = entry_points.select(group="medeval.evaluators")
        else:
            # Python 3.9 API (dict-like)
            medeval_eps = entry_points.get("medeval.evaluators", [])  # pylint: disable=no-member

        for ep in medeval_eps:
            try:
                evaluator_class = ep.load()
                if issubclass(evaluator_class, Evaluator):
                    discovered[ep.name] = evaluator_class
                    logger.info(f"Discovered evaluator plugin: {ep.name}")
                else:
                    logger.warning(f"Entry point {ep.name} does not point to an Evaluator subclass")
            except Exception as e:  # pylint: disable=broad-exception-caught
                # A single malformed/broken third-party plugin must not prevent
                # discovery of the remaining plugins or the built-in evaluators.
                logger.error(f"Failed to load evaluator plugin {ep.name}: {e}")

    except Exception as e:  # pylint: disable=broad-exception-caught
        # entry_points() behavior varies across Python/importlib_metadata
        # versions; any failure here should degrade to "no plugins found"
        # rather than crash evaluator discovery.
        logger.debug(f"Could not discover plugins: {e}")

    return discovered


def list_available_evaluators() -> list[str]:
    """List all available evaluator names (built-in + plugins).

    Returns:
        List of evaluator names that can be instantiated.
    """
    # Imported here (not at module top) to avoid a circular import: this
    # module (medeval.evaluators.base) is imported by medeval.evaluators.__init__,
    # so importing from medeval.evaluators at module scope would fail.
    from medeval.evaluators import (  # pylint: disable=import-outside-toplevel
        CalibrationEvaluator,
        EntityExtractionEvaluator,
        ForbiddenFactsEvaluator,
        FormatValidator,
        LLMJudgeEvaluator,
        MedicationF1Evaluator,
        RequiredFactsEvaluator,
    )

    # Built-in evaluators
    built_in = {
        "medication_f1": MedicationF1Evaluator,
        "format_validator": FormatValidator,
        "entity_extraction": EntityExtractionEvaluator,
        "calibration": CalibrationEvaluator,
        "required_facts": RequiredFactsEvaluator,
        "forbidden_facts": ForbiddenFactsEvaluator,
        "llm_judge": LLMJudgeEvaluator,
    }

    # Discover plugins
    plugins = discover_evaluators()

    # Combine (plugins can override built-ins)
    all_evaluators = {**built_in, **plugins}

    return sorted(all_evaluators.keys())
