"""Evaluator that uses the LLM as a judge."""

import logging
from typing import Any

from medeval.evaluators.base import Evaluator
from medeval.llm_judge import DeterministicJudge, LLMJudge
from medeval.models import ClinicalCase, Prediction

# Module logger
logger = logging.getLogger("medeval.evaluators.llm_judge")


class LLMJudgeEvaluator(Evaluator):
    """Evaluator that uses an LLM to assign a similarity score between gold and prediction.

    The evaluator wraps an LLMJudge (deterministic in tests) and exposes the
    'llm_judge_score' metric.
    """

    def __init__(self, llm_judge: LLMJudge | None = None):
        """Initialize with an optional LLMJudge.

        If llm_judge is None, a default deterministic judge is instantiated,
        which makes unit tests reliable.
        """
        super().__init__()
        self.llm = llm_judge or DeterministicJudge()

    def evaluate(self, case: ClinicalCase, prediction: Prediction) -> dict[str, Any]:
        """Produce a single-score evaluation for the prediction.

        Returns:
            Dictionary containing key 'llm_judge_score' mapping to a float in [0,1].
        """
        logger.debug(f"Running LLM judge for case {case.id}")

        gold_text = case.gold_summary.get("summary_text", "") if case.gold_summary else ""
        score = self.llm.judge(gold_text, prediction.summary_text)

        logger.debug(f"LLM judge score: {score:.3f}")

        return {"llm_judge_score": score}
