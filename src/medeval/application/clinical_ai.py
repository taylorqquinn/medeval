"""A tiny clinical AI wrapper used as the system under test."""

import logging
from typing import Optional
from medeval.models import ClinicalCase, Prediction
from medeval.application.llm_client import LLMClient

logger = logging.getLogger('medeval.clinical_ai')


class ClinicalAI:
    """Simple AI that 'summarizes' clinical cases.

    This is intentionally minimal — the focus is the testing infrastructure.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize ClinicalAI with an LLM client.
        
        Args:
            llm_client: Optional LLM client. If None, uses default LLMClient.
        """
        self.llm = llm_client or LLMClient()
        logger.debug(f"ClinicalAI initialized with {type(self.llm).__name__}")

    def summarize(self, case: ClinicalCase) -> Prediction:
        """Produce a deterministic summary for a clinical case.

        The implementation concatenates the symptoms and medications and then
        passes that short prompt to the (deterministic) LLM client.
        
        Args:
            case: ClinicalCase to summarize.
        
        Returns:
            Prediction object with summary_text, medications, and confidence.
        """
        logger.debug(f"Summarizing case {case.id}")
        
        prompt_parts = []
        if case.symptoms:
            prompt_parts.append("Symptoms: " + ", ".join(case.symptoms))
            logger.debug(f"  Added {len(case.symptoms)} symptom(s) to prompt")
        if case.medications:
            prompt_parts.append("Medications: " + ", ".join(case.medications))
            logger.debug(f"  Added {len(case.medications)} medication(s) to prompt")
        
        prompt = ". ".join(prompt_parts)
        logger.debug(f"  Prompt length: {len(prompt)} chars")
        
        summary_text = self.llm.generate(prompt)
        logger.debug(f"  Generated summary: {len(summary_text)} chars")
        
        # Attach structured medications so evaluators can compute medication F1.
        tokens = summary_text.split()
        confidence = min(1.0, max(0.0, len(tokens) / 80.0))
        
        prediction = Prediction(
            case_id=case.id,
            summary_text=summary_text,
            medications=list(case.medications),
            confidence=confidence
        )
        
        logger.debug(f"  Prediction confidence: {confidence:.3f}")
        logger.info(f"Completed summarization for case {case.id}")
        
        return prediction
