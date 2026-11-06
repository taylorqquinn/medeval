"""Medication F1 evaluator for structured medication lists."""

import logging
from typing import Any

from medeval.evaluators.base import Evaluator
from medeval.models import ClinicalCase, Prediction

# Module logger
logger = logging.getLogger("medeval.evaluators.medication_f1")


def _normalize_med_list(lst):
    """Normalize a list of medication strings into a canonical set.

    Converts medication names to lowercase and strips surrounding whitespace,
    removing duplicates by returning a set. If lst is None, returns an empty set.

    This is intentionally conservative and does not attempt any pharmacological
    normalization (no stemming, no synonym resolution). It is intended to make
    simple string-comparison evaluation deterministic in tests.
    """
    return set(m.lower().strip() for m in (lst or []))


class MedicationF1Evaluator(Evaluator):
    """Evaluator that computes precision, recall, and F1 for medication lists.

    The evaluator compares structured medication lists (gold vs prediction) after
    normalization. Edge cases are handled deterministically:
      - If prediction list is empty:
          * precision = 1.0 if gold is also empty else 0.0
      - If gold list is empty:
          * recall = 1.0
    """

    def evaluate(self, case: ClinicalCase, prediction: Prediction) -> dict[str, Any]:
        """Evaluate medication overlap for a single case.

        Args:
            case: ClinicalCase with a .medications attribute (list of strings).
            prediction: Prediction with a .medications attribute (list of strings).

        Returns:
            A dict with keys:
              - med_precision: float
              - med_recall: float
              - med_f1: float
        """
        logger.debug(f"Evaluating medication F1 for case {case.id}")

        gold = _normalize_med_list(case.medications)
        pred = _normalize_med_list(prediction.medications)

        logger.debug(f"Gold medications: {gold}")
        logger.debug(f"Predicted medications: {pred}")

        tp = len(gold & pred)
        precision = tp / len(pred) if pred else (1.0 if not gold else 0.0)
        recall = tp / len(gold) if gold else 1.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

        logger.debug(f"TP={tp}, Precision={precision:.3f}, Recall={recall:.3f}, F1={f1:.3f}")

        return {"med_precision": precision, "med_recall": recall, "med_f1": f1}
