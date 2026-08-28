"""Evaluator that uses the LLM as a judge (simulated)."""

import logging
from medeval.evaluators.base import Evaluator
from medeval.models import ClinicalCase, Prediction
from medeval.application.llm_client import LLMClient
from typing import Dict, Any, Optional

# Module logger
logger = logging.getLogger('medeval.evaluators.llm_judge')


class LLMJudgeEvaluator(Evaluator):
    """Evaluator that uses an LLM to assign a similarity score between gold and prediction.

    The evaluator wraps an LLMClient (deterministic in tests) and exposes the
    'llm_judge_score' metric.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize with an optional LLMClient.

        If llm_client is None, a default deterministic LLMClient is instantiated,
        which makes unit tests reliable.
        """
        self.llm = llm_client or LLMClient()

    def evaluate(self, case: ClinicalCase, prediction: Prediction) -> Dict[str, Any]:
        """Produce a single-score evaluation for the prediction.

        Returns:
            Dictionary containing key 'llm_judge_score' mapping to a float in [0,1].
        """
        logger.debug(f"Running LLM judge for case {case.id}")
        
        gold_text = case.gold_summary.get("summary_text", "") if case.gold_summary else ""
        score = self.llm.judge(gold_text, prediction.summary_text)
        
        logger.debug(f"LLM judge score: {score:.3f}")
        
        return {"llm_judge_score": score}
