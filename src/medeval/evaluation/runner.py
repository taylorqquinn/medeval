"""Simplified evaluation runner for the framework.

This module provides a clean, framework-focused evaluation runner that takes
cases and predictions and applies evaluators to them. It does NOT generate
predictions (that's application logic - see medeval-helpers).
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from medeval.evaluators.base import Evaluator
from medeval.models import ClinicalCase, Prediction

logger = logging.getLogger(__name__)


@dataclass
class CaseResult:
    """Results from evaluating a single case."""

    case_id: str
    metrics: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


@dataclass
class EvaluationResults:
    """Results from evaluating multiple cases."""

    case_results: list[CaseResult] = field(default_factory=list)
    aggregated_metrics: dict[str, Any] = field(default_factory=dict)
    quality_gate_passed: bool | None = None


class EvaluationRunner:
    """Evaluation runner that applies evaluators to cases and predictions.

    This is a framework-level runner that focuses on evaluation logic only.
    It does NOT:
    - Generate predictions (that's application logic)
    - Handle logging/artifacts (that's helper utilities)
    - Interact with LLMs directly (use application/openai_client for that)

    Example:
        from medeval.evaluation.runner import EvaluationRunner
        from medeval.evaluators import MedicationF1Evaluator

        runner = EvaluationRunner(evaluators=[MedicationF1Evaluator()])
        results = runner.run(cases, predictions)
        print(results.aggregated_metrics)
    """

    def __init__(
        self,
        evaluators: list[Evaluator],
        baseline_path: str | None = None,
        quality_gate_threshold: float = 0.8,
    ):
        """Initialize the evaluation runner.

        Args:
            evaluators: List of evaluator instances to apply
            baseline_path: Optional path to baseline metrics (for quality gate)
            quality_gate_threshold: Threshold for passing quality gate
        """
        self.evaluators = evaluators
        self.baseline_path = baseline_path
        self.quality_gate_threshold = quality_gate_threshold

        logger.info(f"Initialized EvaluationRunner with {len(evaluators)} evaluator(s)")

    def evaluate_case(self, case: ClinicalCase, prediction: Prediction) -> CaseResult:
        """Evaluate a single case-prediction pair.

        Args:
            case: Clinical case with ground truth
            prediction: Model prediction to evaluate

        Returns:
            CaseResult with metrics and any errors
        """
        result = CaseResult(case_id=case.id)

        for evaluator in self.evaluators:
            try:
                metrics = evaluator.evaluate(case, prediction)
                result.metrics.update(metrics)
                logger.debug(f"Case {case.id}: {evaluator.name} returned {len(metrics)} metric(s)")
            except Exception as e:
                error_msg = f"{evaluator.name} failed: {str(e)}"
                result.errors.append(error_msg)
                logger.error(f"Case {case.id}: {error_msg}")

        return result

    def run(self, cases: list[ClinicalCase], predictions: list[Prediction]) -> EvaluationResults:
        """Run evaluation on a list of cases and predictions.

        Args:
            cases: List of clinical cases
            predictions: List of predictions (must match cases by case_id)

        Returns:
            EvaluationResults with per-case and aggregated metrics

        Raises:
            ValueError: If cases and predictions don't match
        """
        logger.info(f"Starting evaluation: {len(cases)} case(s), {len(predictions)} prediction(s)")

        # Validate inputs
        if len(cases) != len(predictions):
            raise ValueError(f"Number of cases ({len(cases)}) != predictions ({len(predictions)})")

        # Create case_id to prediction mapping
        pred_map = {p.case_id: p for p in predictions}

        # Evaluate each case
        case_results = []
        for case in cases:
            if case.id not in pred_map:
                logger.warning(f"No prediction found for case {case.id}, skipping")
                continue

            prediction = pred_map[case.id]
            result = self.evaluate_case(case, prediction)
            case_results.append(result)

        logger.info(f"Evaluated {len(case_results)} case(s)")

        # Aggregate metrics
        aggregated = self._aggregate_metrics(case_results)

        # Evaluate quality gate if baseline provided
        quality_gate_passed = None
        if self.baseline_path:
            quality_gate_passed = self._evaluate_quality_gate(aggregated)

        return EvaluationResults(
            case_results=case_results,
            aggregated_metrics=aggregated,
            quality_gate_passed=quality_gate_passed,
        )

    def _aggregate_metrics(self, case_results: list[CaseResult]) -> dict[str, Any]:
        """Aggregate metrics across all cases.

        Args:
            case_results: List of per-case results

        Returns:
            Dictionary of aggregated metrics
        """
        if not case_results:
            return {}

        # Collect all metrics by key
        metrics_by_key: dict[str, list[float]] = {}

        for result in case_results:
            for key, value in result.metrics.items():
                if isinstance(value, (int, float)):
                    if key not in metrics_by_key:
                        metrics_by_key[key] = []
                    metrics_by_key[key].append(float(value))

        # Calculate averages
        aggregated = {}
        for key, values in metrics_by_key.items():
            if values:
                aggregated[f"{key}_mean"] = sum(values) / len(values)
                aggregated[f"{key}_min"] = min(values)
                aggregated[f"{key}_max"] = max(values)

        logger.info(f"Aggregated {len(aggregated)} metric(s)")
        return aggregated

    def _evaluate_quality_gate(self, aggregated: dict[str, Any]) -> bool:
        """Evaluate whether aggregated metrics pass quality gate.

        Args:
            aggregated: Aggregated metrics

        Returns:
            True if quality gate passed, False otherwise
        """
        # Simplified quality gate: check if mean metrics exceed threshold
        # Real implementation would load baseline from file and compare

        mean_metrics = {k: v for k, v in aggregated.items() if "_mean" in k}

        if not mean_metrics:
            logger.warning("No mean metrics to evaluate quality gate")
            return False

        passing_count = sum(1 for v in mean_metrics.values() if v >= self.quality_gate_threshold)
        passed = passing_count == len(mean_metrics)

        logger.info(
            f"Quality gate: {passing_count}/{len(mean_metrics)} metrics passed "
            f"(threshold={self.quality_gate_threshold})"
        )

        return passed


# Legacy function for backwards compatibility
def run(dataset_path: str, baseline_path: str | None = None, **kwargs) -> dict[str, Any]:
    """Legacy run function for backwards compatibility.

    NOTE: This function requires application dependencies (ClinicalAI, LLMClient)
    which are not part of the framework. Use EvaluationRunner class instead.

    This function is kept for backwards compatibility but will raise an error
    directing users to the new API or to install medeval-helpers.
    """
    raise NotImplementedError(
        "The legacy run() function requires application dependencies "
        "(ClinicalAI, LLMClient) which have been moved to medeval-helpers.\n\n"
        "Use the new EvaluationRunner API instead:\n"
        "  from medeval.evaluation.runner import EvaluationRunner\n"
        "  runner = EvaluationRunner(evaluators=[...])\n"
        "  results = runner.run(cases, predictions)\n\n"
        "Or install medeval-helpers for CLI tools:\n"
        "  pip install medeval-helpers\n"
        "  medeval run --dataset cases.jsonl\n"
    )
