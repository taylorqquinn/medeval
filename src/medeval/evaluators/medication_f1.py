"""Medication F1 evaluator for structured medication lists."""

from medeval.evaluators.base import Evaluator
from medeval.models import ClinicalCase, Prediction
from typing import Dict, Any

def _normalize_med_list(lst):
    return set([m.lower().strip() for m in (lst or [])])

class MedicationF1Evaluator(Evaluator):
    def evaluate(self, case: ClinicalCase, prediction: Prediction) -> Dict[str, Any]:
        gold = _normalize_med_list(case.medications)
        pred = _normalize_med_list(prediction.medications)
        tp = len(gold & pred)
        precision = tp / len(pred) if pred else (1.0 if not gold else 0.0)
        recall = tp / len(gold) if gold else 1.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        return {"med_precision": precision, "med_recall": recall, "med_f1": f1}
