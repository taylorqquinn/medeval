"""A tiny clinical AI wrapper used as the system under test."""

from typing import Optional
from medeval.models import ClinicalCase, Prediction
from medeval.application.llm_client import LLMClient

class ClinicalAI:
    """Simple AI that 'summarizes' clinical cases.

    This is intentionally minimal — the focus is the testing infrastructure.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def summarize(self, case: ClinicalCase) -> Prediction:
        """Produce a deterministic summary for a clinical case.

        The implementation concatenates the symptoms and medications and then
        passes that short prompt to the (deterministic) LLM client.
        """
        prompt_parts = []
        if case.symptoms:
            prompt_parts.append("Symptoms: " + ", ".join(case.symptoms))
        if case.medications:
            prompt_parts.append("Medications: " + ", ".join(case.medications))
        prompt = ". ".join(prompt_parts)
        summary_text = self.llm.generate(prompt)
        # Attach structured medications so evaluators can compute medication F1.
        tokens = summary_text.split()
        confidence = min(1.0, max(0.0, len(tokens) / 80.0))
        return Prediction(case_id=case.id, summary_text=summary_text, medications=list(case.medications), confidence=confidence)
