"""Performance and reliability evaluators.

This module provides evaluators for production metrics: latency, cost,
throughput, and reliability. Essential for monitoring AI systems in production.
"""

import logging
from typing import Any

from medeval.evaluators.base import Evaluator
from medeval.models import ClinicalCase, Prediction

logger = logging.getLogger("medeval.evaluators.performance")


class PerformanceEvaluator(Evaluator):
    """Evaluator for performance metrics (latency, cost, throughput).

    Tracks operational metrics essential for production AI systems:
    - Latency: Response time in milliseconds
    - Cost: API cost per prediction in USD
    - Tokens: Token usage for LLM-based systems
    - Throughput: Predictions per second (calculated at aggregate level)

    These metrics help teams:
    - Set SLAs (e.g., p95 latency < 500ms)
    - Monitor costs and optimize spend
    - Detect performance regressions
    - Make deployment decisions (e.g., smaller model for cost)

    Requires:
        - Prediction.latency_ms: Response time in milliseconds
        - Prediction.cost_usd: Cost per prediction (optional)
        - Prediction.tokens_used: Total tokens (optional)

    Returns:
        - latency_ms: float
        - cost_usd: float
        - tokens_used: int
        - passed_latency_sla: bool (if SLA threshold set)
        - passed_cost_sla: bool (if SLA threshold set)
    """

    def __init__(self, latency_sla_ms: float | None = None, cost_sla_usd: float | None = None):
        """Initialize the performance evaluator.

        Args:
            latency_sla_ms: Maximum acceptable latency in milliseconds
            cost_sla_usd: Maximum acceptable cost per prediction in USD
        """
        super().__init__()
        self.latency_sla_ms = latency_sla_ms
        self.cost_sla_usd = cost_sla_usd

    def evaluate(self, case: ClinicalCase, prediction: Prediction) -> dict[str, Any]:
        """Evaluate performance metrics for a prediction.

        Args:
            case: ClinicalCase (not used for performance, but required by interface)
            prediction: Prediction with latency_ms, cost_usd, tokens_used fields

        Returns:
            Dictionary with performance metrics
        """
        logger.debug(f"Evaluating performance for case {case.id}")

        # Extract performance metrics from prediction
        latency_ms = getattr(prediction, "latency_ms", None)
        cost_usd = getattr(prediction, "cost_usd", None)
        tokens_used = getattr(prediction, "tokens_used", None)

        # Check SLA compliance
        passed_latency_sla = None
        if latency_ms is not None and self.latency_sla_ms is not None:
            passed_latency_sla = latency_ms <= self.latency_sla_ms
            if not passed_latency_sla:
                logger.warning(
                    f"Latency SLA violation: {latency_ms:.1f}ms > {self.latency_sla_ms}ms"
                )

        passed_cost_sla = None
        if cost_usd is not None and self.cost_sla_usd is not None:
            passed_cost_sla = cost_usd <= self.cost_sla_usd
            if not passed_cost_sla:
                logger.warning(f"Cost SLA violation: ${cost_usd:.4f} > ${self.cost_sla_usd:.4f}")

        logger.debug(
            f"Performance - Latency: {latency_ms}ms, "
            f"Cost: ${cost_usd if cost_usd else 'N/A'}, "
            f"Tokens: {tokens_used if tokens_used else 'N/A'}"
        )

        return {
            "latency_ms": latency_ms,
            "cost_usd": cost_usd,
            "tokens_used": tokens_used,
            "passed_latency_sla": passed_latency_sla,
            "passed_cost_sla": passed_cost_sla,
        }


class ReliabilityEvaluator(Evaluator):
    """Evaluator for reliability metrics (errors, timeouts, availability).

    Tracks system reliability metrics:
    - Error rate: Predictions that failed or returned errors
    - Timeout rate: Predictions that exceeded time limit
    - Availability: Successfully completed predictions
    - Retry success: Whether retries succeeded

    These metrics help teams:
    - Monitor system health
    - Set uptime SLAs (e.g., 99.9% availability)
    - Detect infrastructure issues
    - Implement retry strategies

    A prediction is considered "failed" if:
    - It has an empty or error-like summary_text
    - It has safety_flags indicating errors
    - It took longer than timeout threshold

    Returns:
        - prediction_succeeded: bool
        - is_error: bool
        - is_timeout: bool (if timeout threshold set)
        - error_type: str (if error detected)
        - retry_count: int (if tracked)
    """

    def __init__(self, timeout_threshold_ms: float | None = None):
        """Initialize the reliability evaluator.

        Args:
            timeout_threshold_ms: Maximum acceptable latency before considering it a timeout
        """
        super().__init__()
        self.timeout_threshold_ms = timeout_threshold_ms

    def evaluate(self, case: ClinicalCase, prediction: Prediction) -> dict[str, Any]:
        """Evaluate reliability metrics for a prediction.

        Args:
            case: ClinicalCase
            prediction: Prediction to check for errors/timeouts

        Returns:
            Dictionary with reliability metrics
        """
        logger.debug(f"Evaluating reliability for case {case.id}")

        # Check if prediction succeeded
        is_error = self._is_error_prediction(prediction)

        # Check for timeout
        is_timeout = False
        latency_ms = getattr(prediction, "latency_ms", None)
        if latency_ms is not None and self.timeout_threshold_ms is not None:
            is_timeout = latency_ms > self.timeout_threshold_ms

        # Determine error type
        error_type = None
        if is_error:
            error_type = self._detect_error_type(prediction)

        # Overall success
        prediction_succeeded = not (is_error or is_timeout)

        if not prediction_succeeded:
            logger.warning(
                f"Prediction failed - Error: {is_error}, Timeout: {is_timeout}, "
                f"Type: {error_type}"
            )

        return {
            "prediction_succeeded": prediction_succeeded,
            "is_error": is_error,
            "is_timeout": is_timeout,
            "error_type": error_type,
            "availability": 1.0 if prediction_succeeded else 0.0,
        }

    def _is_error_prediction(self, prediction: Prediction) -> bool:
        """Check if prediction represents an error."""
        # Empty or very short output
        if not prediction.summary_text or len(prediction.summary_text.strip()) < 5:
            return True

        # Check for error indicators in text
        error_indicators = [
            "error",
            "failed",
            "exception",
            "unable to process",
            "internal error",
            "service unavailable",
        ]

        text_lower = prediction.summary_text.lower()
        if any(indicator in text_lower for indicator in error_indicators):
            return True

        # Check safety flags for errors
        if hasattr(prediction, "safety_flags") and prediction.safety_flags:
            error_flags = ["error", "timeout", "rate_limit", "service_error"]
            if any(flag in prediction.safety_flags for flag in error_flags):
                return True

        return False

    def _detect_error_type(self, prediction: Prediction) -> str | None:
        """Detect the type of error from prediction."""
        text_lower = prediction.summary_text.lower() if prediction.summary_text else ""

        if "timeout" in text_lower or "timed out" in text_lower:
            return "timeout"
        if "rate limit" in text_lower:
            return "rate_limit"
        if "authentication" in text_lower or "unauthorized" in text_lower:
            return "auth_error"
        if "service unavailable" in text_lower or "503" in text_lower:
            return "service_unavailable"
        if "internal error" in text_lower or "500" in text_lower:
            return "internal_error"
        return "unknown_error"
