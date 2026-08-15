"""Evaluator that heuristically extracts entities from the summary text and scores extraction."""

from medeval.evaluators.base import Evaluator
from medeval.models import ClinicalCase, Prediction
from typing import Dict, Any

def _normalize_list(lst):
    return set([s.lower().strip() for s in (lst or [])])

class EntityExtractionEvaluator(Evaluator):
    def evaluate(self, case: ClinicalCase, prediction: Prediction) -> Dict[str, Any]:
        text = (prediction.summary_text or "").lower()

        # Medications: attempt to parse a 'Medications:' section and split by commas
        predicted_meds = set()
        if "medications:" in text:
            med_part = text.split("medications:", 1)[1]
            med_part = med_part.split(".", 1)[0]
            tokens = [m.strip().strip(".") for m in med_part.split(",") if m.strip()]
            predicted_meds = set([t.lower() for t in tokens])

        gold_meds = _normalize_list(case.medications)
        tp_meds = len(gold_meds & predicted_meds)
        med_precision = tp_meds / len(predicted_meds) if predicted_meds else (1.0 if not gold_meds else 0.0)
        med_recall = tp_meds / len(gold_meds) if gold_meds else 1.0
        med_f1 = (2 * med_precision * med_recall / (med_precision + med_recall)) if (med_precision + med_recall) else 0.0

        # Symptoms: attempt to parse a 'Symptoms:' section
        predicted_symptoms = set()
        if "symptoms:" in text:
            sym_part = text.split("symptoms:", 1)[1]
            sym_part = sym_part.split(".", 1)[0]
            tokens = [s.strip().strip(".") for s in sym_part.split(",") if s.strip()]
            predicted_symptoms = set([t.lower() for t in tokens])

        gold_symptoms = _normalize_list(case.symptoms)
        tp_sym = len(gold_symptoms & predicted_symptoms)
        sym_precision = tp_sym / len(predicted_symptoms) if predicted_symptoms else (1.0 if not gold_symptoms else 0.0)
        sym_recall = tp_sym / len(gold_symptoms) if gold_symptoms else 1.0
        sym_f1 = (2 * sym_precision * sym_recall / (sym_precision + sym_recall)) if (sym_precision + sym_recall) else 0.0

        return {
            "entity_med_precision": med_precision,
            "entity_med_recall": med_recall,
            "entity_med_f1": med_f1,
            "entity_symptom_precision": sym_precision,
            "entity_symptom_recall": sym_recall,
            "entity_symptom_f1": sym_f1,
        }
