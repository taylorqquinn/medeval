"""Evaluator that heuristically extracts entities from the summary text and scores extraction."""

import logging
from typing import Any

from medeval.evaluators.base import Evaluator
from medeval.models import ClinicalCase, Prediction

# Module logger
logger = logging.getLogger("medeval.evaluators.entity_extraction")


def _normalize_list(lst):
    """Normalize a list of strings to a set of lowercase, stripped tokens.

    This helper is used to compare gold lists against predicted extractions.
    """
    return set(s.lower().strip() for s in (lst or []))


class EntityExtractionEvaluator(Evaluator):
    """Heuristic extractor evaluator for simple 'Symptoms:' and 'Medications:' sections.

    The evaluator searches the prediction.summary_text for 'Symptoms:' and
    'Medications:' markers, takes the text following the marker up to the next
    period, splits on commas, and normalizes tokens. It then computes precision,
    recall, and F1 for each entity type against the gold lists provided in the case.
    """

    def evaluate(self, case: ClinicalCase, prediction: Prediction) -> dict[str, Any]:
        """Extract entities heuristically from the summary and score them.

        Args:
            case: ClinicalCase containing lists case.symptoms and case.medications.
            prediction: Prediction containing a 'summary_text' which may include 'Symptoms:'
                        and/or 'Medications:' sections.

        Returns:
            Dict with keys:
              - entity_med_precision, entity_med_recall, entity_med_f1
              - entity_symptom_precision, entity_symptom_recall, entity_symptom_f1
        """
        logger.debug(f"Extracting entities for case {case.id}")
        text = (prediction.summary_text or "").lower()

        # Medications: attempt to parse a 'Medications:' section and split by commas
        predicted_meds = set()
        if "medications:" in text:
            med_part = text.split("medications:", 1)[1]
            med_part = med_part.split(".", 1)[0]
            tokens = [m.strip().strip(".") for m in med_part.split(",") if m.strip()]
            predicted_meds = set(t.lower() for t in tokens)

        gold_meds = _normalize_list(case.medications)
        tp_meds = len(gold_meds & predicted_meds)
        med_precision = (
            tp_meds / len(predicted_meds) if predicted_meds else (1.0 if not gold_meds else 0.0)
        )
        med_recall = tp_meds / len(gold_meds) if gold_meds else 1.0
        med_f1 = (
            (2 * med_precision * med_recall / (med_precision + med_recall))
            if (med_precision + med_recall)
            else 0.0
        )

        logger.debug(f"Meds - Predicted: {predicted_meds}, Gold: {gold_meds}, F1: {med_f1:.3f}")

        # Symptoms: attempt to parse a 'Symptoms:' section
        predicted_symptoms = set()
        if "symptoms:" in text:
            sym_part = text.split("symptoms:", 1)[1]
            sym_part = sym_part.split(".", 1)[0]
            tokens = [s.strip().strip(".") for s in sym_part.split(",") if s.strip()]
            predicted_symptoms = set(t.lower() for t in tokens)

        gold_symptoms = _normalize_list(case.symptoms)
        tp_sym = len(gold_symptoms & predicted_symptoms)
        sym_precision = (
            tp_sym / len(predicted_symptoms)
            if predicted_symptoms
            else (1.0 if not gold_symptoms else 0.0)
        )
        sym_recall = tp_sym / len(gold_symptoms) if gold_symptoms else 1.0
        sym_f1 = (
            (2 * sym_precision * sym_recall / (sym_precision + sym_recall))
            if (sym_precision + sym_recall)
            else 0.0
        )

        logger.debug(
            f"Symptoms - Predicted: {predicted_symptoms}, Gold: {gold_symptoms}, F1: {sym_f1:.3f}"
        )

        return {
            "entity_med_precision": med_precision,
            "entity_med_recall": med_recall,
            "entity_med_f1": med_f1,
            "entity_symptom_precision": sym_precision,
            "entity_symptom_recall": sym_recall,
            "entity_symptom_f1": sym_f1,
        }
