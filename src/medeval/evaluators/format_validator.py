"""Evaluator that checks summary text format and length."""

from medeval.evaluators.base import Evaluator
from medeval.models import ClinicalCase, Prediction
from typing import Dict, Any

class FormatValidator(Evaluator):
    def __init__(self, require_med_section: bool = True, max_length: int = 1000):
        self.require_med_section = require_med_section
        self.max_length = max_length

    def evaluate(self, case: ClinicalCase, prediction: Prediction) -> Dict[str, Any]:
        text = (prediction.summary_text or "")
        errors = []
        if self.require_med_section and "Medications:" not in text:
            errors.append("missing_medications_section")
        length_ok = len(text) <= self.max_length
        if not length_ok:
            errors.append("summary_too_long")
        score = 1.0 if not errors else 0.0
        return {"format_score": score, "format_errors": errors, "summary_length": len(text)}
