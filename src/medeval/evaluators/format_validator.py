"""Evaluator that checks summary text format and length."""

import logging
from medeval.evaluators.base import Evaluator
from medeval.models import ClinicalCase, Prediction
from typing import Dict, Any

# Module logger
logger = logging.getLogger('medeval.evaluators.format_validator')


class FormatValidator(Evaluator):
    """Validator that checks that the generated summary follows expected format.

    Two checks are performed:
      1. presence of a 'Medications:' section if require_med_section is True
      2. summary length is <= max_length characters

    The evaluator returns a binary 'format_score' (1.0 if no errors, else 0.0),
    a list of format error codes, and the observed summary length.
    """

    def __init__(self, require_med_section: bool = True, max_length: int = 1000):
        """Construct a FormatValidator.

        Args:
            require_med_section: If True, require the substring 'Medications:' in the summary.
            max_length: Maximum allowed summary length in characters; summaries longer than
                        this are considered invalid and will produce the 'summary_too_long' error.
        """
        self.require_med_section = require_med_section
        self.max_length = max_length

    def evaluate(self, case: ClinicalCase, prediction: Prediction) -> Dict[str, Any]:
        """Validate the prediction summary for format constraints.

        Args:
            case: ClinicalCase (present for interface compatibility; unused).
            prediction: Prediction containing a 'summary_text' string.

        Returns:
            Dict with keys:
              - format_score: float (1.0 when no errors)
              - format_errors: List[str] of error codes (empty when score == 1.0)
              - summary_length: int length of the summary_text
        """
        logger.debug(f"Validating format for case {case.id}")
        
        text = (prediction.summary_text or "")
        errors = []
        
        if self.require_med_section and "Medications:" not in text:
            errors.append("missing_medications_section")
            logger.debug("Missing medications section")
            
        length_ok = len(text) <= self.max_length
        if not length_ok:
            errors.append("summary_too_long")
            logger.debug(f"Summary too long: {len(text)} > {self.max_length}")
            
        score = 1.0 if not errors else 0.0
        logger.debug(f"Format score: {score}, errors: {errors}, length: {len(text)}")
        
        return {"format_score": score, "format_errors": errors, "summary_length": len(text)}
