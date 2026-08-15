import os
import sys
import pytest
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from medeval.models import ClinicalCase, Prediction
from medeval.evaluators.format_validator import FormatValidator


def test_format_validator_missing_and_present():
    case = ClinicalCase(id='f1', text='', symptoms=[], medications=[], required_facts=[], forbidden_facts=[], gold_summary={})
    pred1 = Prediction(case_id='f1', summary_text='This has no meds section.', medications=[])
    pred2 = Prediction(case_id='f1', summary_text='Medications: aspirin.', medications=['aspirin'])
    ev = FormatValidator()
    r1 = ev.evaluate(case, pred1)
    r2 = ev.evaluate(case, pred2)
    assert r1['format_score'] == pytest.approx(0.0)
    assert r2['format_score'] == pytest.approx(1.0)
