"""Calibration evaluator that emits per-case confidence and correctness.

The dataset-level calibration error (ECE) is computed later by the metrics aggregator.
"""

from medeval.evaluators.base import Evaluator
from medeval.models import ClinicalCase, Prediction
from typing import Dict, Any, Optional
from medeval.application.llm_client import LLMClient

class CalibrationEvaluator(Evaluator):
    def __init__(self, llm_client: Optional[LLMClient] = None, threshold: float = 0.5):
        self.llm = llm_client or LLMClient()
        self.threshold = threshold

    def evaluate(self, case: ClinicalCase, prediction: Prediction) -> Dict[str, Any]:
        confidence = float(prediction.confidence) if getattr(prediction, 'confidence', None) is not None else 0.5
        gold_text = case.gold_summary.get("summary_text", "") if case.gold_summary else ""
        judge_score = self.llm.judge(gold_text, prediction.summary_text)
        is_correct = 1.0 if judge_score >= self.threshold else 0.0
        return {"confidence": confidence, "is_correct": is_correct, "judge_score": judge_score}
