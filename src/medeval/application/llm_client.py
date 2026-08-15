"""Minimal LLM client used by the example clinical AI.

This is intentionally simplistic and deterministic so tests are reliable.
"""

from typing import Optional

class LLMClient:
    """A tiny, deterministic LLM-like client used for testing."""

    def generate(self, prompt: str) -> str:
        """Generate a short deterministic summary from the prompt.

        The real system would call an external LLM. Here we keep things
        deterministic for unit tests and CI.
        """
        # Naive summarization: keep the first 80 tokens
        tokens = prompt.split()
        return " ".join(tokens[:80])

    def judge(self, gold: str, pred: str) -> float:
        """Return a simple overlap-based score between 0.0 and 1.0.

        Measures fraction of unique gold tokens that appear in prediction.
        """
        gold_set = set(gold.lower().split())
        pred_set = set(pred.lower().split())
        if not gold_set:
            return 1.0 if not pred_set else 0.0
        return len(gold_set & pred_set) / len(gold_set)
