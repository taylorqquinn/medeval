import os
import sys
import pytest
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from medeval.models import ClinicalCase, Prediction
from medeval.evaluators.medication_f1 import MedicationF1Evaluator


def test_medication_f1_basic():
    case = ClinicalCase(id="t1", text="", symptoms=[], medications=["Aspirin","Metformin"], required_facts=[], forbidden_facts=[], gold_summary={})
    pred = Prediction(case_id="t1", summary_text="", medications=["aspirin"])
    ev = MedicationF1Evaluator()
    res = ev.evaluate(case, pred)
    assert res['med_precision'] == pytest.approx(1.0)
    assert res['med_recall'] == pytest.approx(0.5)
    assert res['med_f1'] == pytest.approx(2/3)
