"""Evaluator that ensures forbidden facts are not mentioned."""

import logging
from medeval.evaluators.base import Evaluator
from medeval.models import ClinicalCase, Prediction
from typing import Dict, Any

# Module logger
logger = logging.getLogger('medeval.evaluators.forbidden_facts')


class ForbiddenFactsEvaluator(Evaluator):
    """Evaluator that ensures forbidden facts are not mentioned.

    Reports a binary score (1.0 when no forbidden facts found) and the list of found items.
    """

    def evaluate(self, case: ClinicalCase, prediction: Prediction) -> Dict[str, Any]:
        """Find forbidden facts mentioned in the prediction text.

        Args:
            case: ClinicalCase with .forbidden_facts list
            prediction: Prediction with .summary_text

        Returns:
            Dict with keys:
              - forbidden_score: 1.0 if none of the forbidden facts are present, else 0.0
              - forbidden_found: list of forbidden facts that appear in the text
        """
        logger.debug(f"Checking forbidden facts for case {case.id}")
        
        forbidden = case.forbidden_facts or []
        found = [f for f in forbidden if f.lower() in prediction.summary_text.lower()]
        score = 0.0 if found else 1.0
        
        logger.debug(f"Forbidden facts: {len(forbidden)}, Found: {len(found)}, Score: {score:.1f}")
        if found:
            logger.warning(f"Forbidden facts found: {found}")
        
        return {"forbidden_score": score, "forbidden_found": found}
