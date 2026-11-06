"""MedEval Framework - Core evaluation engine for clinical AI systems.

This package provides the core evaluation framework without CLI or helper utilities.
For CLI tools, logging, and configuration management, install medeval-helpers.

Core components:
- models: Data models (ClinicalCase, Prediction, EvaluationResult)
- dataset: Dataset loading utilities
- evaluators: Built-in evaluators and base class for custom evaluators
- evaluation: Evaluation pipeline, metrics, baselines, quality gates

Example usage:
    from medeval.models import ClinicalCase, Prediction
    from medeval.evaluation.runner import EvaluationRunner
    from medeval.evaluators import MedicationF1Evaluator

    runner = EvaluationRunner(evaluators=[MedicationF1Evaluator()])
    results = runner.run(cases, predictions)
"""

__version__ = "0.2.0"

# Core exports
from medeval.dataset import load_dataset
from medeval.evaluation.runner import EvaluationRunner
from medeval.evaluators.base import Evaluator, discover_evaluators
from medeval.models import ClinicalCase, Prediction

__all__ = [
    # Version
    "__version__",
    # Core models
    "ClinicalCase",
    "Prediction",
    # Dataset loading
    "load_dataset",
    # Evaluation
    "EvaluationRunner",
    # Evaluators
    "Evaluator",
    "discover_evaluators",
    # Modules
    "models",
    "dataset",
    "evaluators",
    "evaluation",
]
