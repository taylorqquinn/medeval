"""Simple LLM judge protocol for framework evaluators.

This module defines a minimal interface for LLM-based evaluation without
requiring specific application dependencies. Concrete implementations are
provided in medeval-helpers.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMJudge(Protocol):
    """Protocol for LLM judge implementations.

    This defines the minimal interface needed by framework evaluators that
    use LLM-based judging. Concrete implementations should:
    - Accept gold and prediction text
    - Return a similarity/correctness score in [0, 1]

    Example implementation:
        class MyLLMJudge:
            def judge(self, gold_text: str, pred_text: str) -> float:
                # Your LLM API call here
                return 0.85
    """

    def judge(self, gold_text: str, pred_text: str) -> float:
        """Judge similarity between gold and prediction text.

        Args:
            gold_text: Ground truth text
            pred_text: Prediction text to evaluate

        Returns:
            Float score in [0, 1] where 1.0 means perfect match
        """
        ...


class DeterministicJudge:
    """Deterministic judge for testing (no LLM required).

    Returns a fixed score based on simple text similarity heuristics.
    Useful for unit tests and when no real LLM is available.
    """

    def judge(self, gold_text: str, pred_text: str) -> float:
        """Return deterministic similarity score.

        Uses simple heuristics:
        - If texts are identical: 1.0
        - If prediction contains all gold words: 0.8
        - Otherwise: 0.5
        """
        if not gold_text or not pred_text:
            return 0.5

        gold_lower = gold_text.lower()
        pred_lower = pred_text.lower()

        if gold_lower == pred_lower:
            return 1.0

        # Check if all gold words appear in prediction
        gold_words = set(gold_lower.split())
        pred_words = set(pred_lower.split())

        if gold_words and gold_words.issubset(pred_words):
            return 0.8

        # Default middle score
        return 0.5
