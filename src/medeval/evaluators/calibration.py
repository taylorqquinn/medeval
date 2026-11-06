"""Calibration evaluator that emits per-case confidence and correctness.

The dataset-level calibration error (ECE) is computed later by the metrics aggregator.
"""

import logging
from typing import Any

from medeval.evaluators.base import Evaluator
from medeval.llm_judge import DeterministicJudge, LLMJudge
from medeval.models import ClinicalCase, Prediction

# Module logger
logger = logging.getLogger("medeval.evaluators.calibration")


class CalibrationEvaluator(Evaluator):
    """Evaluator producing per-case confidence and judge-correctness.

    This evaluator consults an LLM judge to determine whether
    the prediction is correct with respect to the gold summary. It returns the
    model-reported confidence, a binary is_correct (1.0/0.0) determined by comparing
    judge_score against the threshold, and the raw judge_score (0.0-1.0).
    """

    def __init__(self, llm_judge: LLMJudge | None = None, threshold: float = 0.5):
        """Initialize the CalibrationEvaluator.

        Args:
            llm_judge: Optional LLMJudge instance used to judge correctness.
                If None, a default deterministic judge is used (suitable for tests).
            threshold: Float threshold in [0,1] above which judge_score is treated as correct.
        """
        super().__init__()
        self.llm = llm_judge or DeterministicJudge()
        self.threshold = threshold

    def evaluate(self, case: ClinicalCase, prediction: Prediction) -> dict[str, Any]:
        """Evaluate calibration-related fields for a single prediction.

        Returns:
            dict with keys:
              - confidence: float model-reported confidence (default 0.5 if missing)
              - is_correct: 1.0 if judge_score >= threshold else 0.0
              - judge_score: raw judge score from LLMJudge.judge in [0.0, 1.0]
        """
        logger.debug(f"Evaluating calibration for case {case.id}")

        confidence = (
            float(prediction.confidence)
            if getattr(prediction, "confidence", None) is not None
            else 0.5
        )
        gold_text = case.gold_summary.get("summary_text", "") if case.gold_summary else ""
        judge_score = self.llm.judge(gold_text, prediction.summary_text)
        is_correct = 1.0 if judge_score >= self.threshold else 0.0

        logger.debug(
            f"Confidence: {confidence:.3f}, Judge score: {judge_score:.3f}, Correct: {is_correct}"
        )

        return {"confidence": confidence, "is_correct": is_correct, "judge_score": judge_score}
