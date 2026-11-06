"""Evaluator that checks required facts are present in the prediction."""

import logging
from medeval.evaluators.base import Evaluator
from medeval.models import ClinicalCase, Prediction
from typing import Dict, Any

# Module logger
logger = logging.getLogger('medeval.evaluators.required_facts')


class RequiredFactsEvaluator(Evaluator):
    """Evaluator that checks required facts are present in the prediction.

    It reports a fraction of required facts present and returns the list of missing facts.
    """

    def evaluate(self, case: ClinicalCase, prediction: Prediction) -> Dict[str, Any]:
        """Check presence of required facts in the prediction text.

        Args:
            case: ClinicalCase with .required_facts list
            prediction: Prediction with .summary_text

        Returns:
            Dict with keys:
              - required_facts_score: fraction of required facts present (1.0 when none required)
              - required_missing: list of missing required fact strings
        """
        logger.debug(f"Checking required facts for case {case.id}")
        
        required = case.required_facts or []
        present = [f for f in required if f.lower() in prediction.summary_text.lower()]
        missing = [f for f in required if f.lower() not in prediction.summary_text.lower()]
        score = len(present) / len(required) if required else 1.0
        
        logger.debug(f"Required facts: {len(required)}, Present: {len(present)}, Missing: {len(missing)}, Score: {score:.3f}")
        if missing:
            logger.debug(f"Missing facts: {missing}")
        
        return {"required_facts_score": score, "required_missing": missing}
