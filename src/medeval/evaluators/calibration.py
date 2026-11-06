"""Calibration evaluator that emits per-case confidence and correctness.

The dataset-level calibration error (ECE) is computed later by the metrics aggregator.
"""

import logging
from medeval.evaluators.base import Evaluator
from medeval.models import ClinicalCase, Prediction
from typing import Dict, Any, Optional
from medeval.application.llm_client import LLMClient

# Module logger
logger = logging.getLogger('medeval.evaluators.calibration')


class CalibrationEvaluator(Evaluator):
    """Evaluator producing per-case confidence and judge-correctness.

    This evaluator consults an LLM judge (via LLMClient) to determine whether
    the prediction is correct with respect to the gold summary. It returns the
    model-reported confidence, a binary is_correct (1.0/0.0) determined by comparing
    judge_score against the threshold, and the raw judge_score (0.0-1.0).
    """

    def __init__(self, llm_client: Optional[LLMClient] = None, threshold: float = 0.5):
        """Initialize the CalibrationEvaluator.

        Args:
            llm_client: Optional LLMClient instance used to judge correctness.
                If None, a default deterministic LLMClient is used (suitable for tests).
            threshold: Float threshold in [0,1] above which judge_score is treated as correct.
        """
        self.llm = llm_client or LLMClient()
        self.threshold = threshold

    def evaluate(self, case: ClinicalCase, prediction: Prediction) -> Dict[str, Any]:
        """Evaluate calibration-related fields for a single prediction.

        Returns:
            dict with keys:
              - confidence: float model-reported confidence (default 0.5 if missing)
              - is_correct: 1.0 if judge_score >= threshold else 0.0
              - judge_score: raw judge score from LLMClient.judge in [0.0, 1.0]
        """
        logger.debug(f"Evaluating calibration for case {case.id}")
        
        confidence = float(prediction.confidence) if getattr(prediction, 'confidence', None) is not None else 0.5
        gold_text = case.gold_summary.get("summary_text", "") if case.gold_summary else ""
        judge_score = self.llm.judge(gold_text, prediction.summary_text)
        is_correct = 1.0 if judge_score >= self.threshold else 0.0
        
        logger.debug(f"Confidence: {confidence:.3f}, Judge score: {judge_score:.3f}, Correct: {is_correct}")
        
        return {"confidence": confidence, "is_correct": is_correct, "judge_score": judge_score}
