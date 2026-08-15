import os
import sys
import pytest
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from medeval.models import ClinicalCase, Prediction
from medeval.evaluators.entity_extraction import EntityExtractionEvaluator


def test_entity_extraction_basic():
    case = ClinicalCase(id='e1', text='', symptoms=['chest pain'], medications=['aspirin','metformin'], required_facts=[], forbidden_facts=[], gold_summary={})
    pred = Prediction(case_id='e1', summary_text='Symptoms: chest pain. Medications: Aspirin, Metformin.', medications=['aspirin','metformin'])
    ev = EntityExtractionEvaluator()
    res = ev.evaluate(case, pred)
    assert res['entity_med_precision'] == pytest.approx(1.0)
    assert res['entity_med_recall'] == pytest.approx(1.0)
    assert res['entity_symptom_precision'] == pytest.approx(1.0)
    assert res['entity_symptom_recall'] == pytest.approx(1.0)
