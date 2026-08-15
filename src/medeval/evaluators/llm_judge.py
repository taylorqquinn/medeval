"""Evaluator that uses the LLM as a judge (simulated)."""

from medeval.evaluators.base import Evaluator
from medeval.models import ClinicalCase, Prediction
from medeval.application.llm_client import LLMClient
from typing import Dict, Any, Optional

class LLMJudgeEvaluator(Evaluator):
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def evaluate(self, case: ClinicalCase, prediction: Prediction) -> Dict[str, Any]:
        gold_text = case.gold_summary.get("summary_text", "") if case.gold_summary else ""
        score = self.llm.judge(gold_text, prediction.summary_text)
        return {"llm_judge_score": score}
