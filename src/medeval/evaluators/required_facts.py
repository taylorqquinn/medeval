"""Evaluator that checks required facts are present in the prediction."""

from medeval.evaluators.base import Evaluator
from medeval.models import ClinicalCase, Prediction
from typing import Dict, Any

class RequiredFactsEvaluator(Evaluator):
    def evaluate(self, case: ClinicalCase, prediction: Prediction) -> Dict[str, Any]:
        required = case.required_facts or []
        present = [f for f in required if f.lower() in prediction.summary_text.lower()]
        missing = [f for f in required if f.lower() not in prediction.summary_text.lower()]
        score = len(present) / len(required) if required else 1.0
        return {"required_facts_score": score, "required_missing": missing}
