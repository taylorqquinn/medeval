"""Evaluator that ensures forbidden facts are not mentioned."""

from medeval.evaluators.base import Evaluator
from medeval.models import ClinicalCase, Prediction
from typing import Dict, Any

class ForbiddenFactsEvaluator(Evaluator):
    def evaluate(self, case: ClinicalCase, prediction: Prediction) -> Dict[str, Any]:
        forbidden = case.forbidden_facts or []
        found = [f for f in forbidden if f.lower() in prediction.summary_text.lower()]
        score = 0.0 if found else 1.0
        return {"forbidden_score": score, "forbidden_found": found}
