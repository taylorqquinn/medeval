"""Tests that document behavior of RequiredFactsEvaluator and ForbiddenFactsEvaluator."""

import os
import sys
import pytest
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from medeval.models import ClinicalCase, Prediction
from medeval.evaluators.required_facts import RequiredFactsEvaluator
from medeval.evaluators.forbidden_facts import ForbiddenFactsEvaluator


def test_required_facts_present_and_missing():
    case = ClinicalCase(id='r1', text='', symptoms=[], medications=[], required_facts=['must1','must2'], forbidden_facts=[], gold_summary={})
    pred = Prediction(case_id='r1', summary_text='Includes must1 but not the other.', medications=[])
    ev = RequiredFactsEvaluator()
    res = ev.evaluate(case, pred)
    assert res['required_facts_score'] == pytest.approx(0.5)
    assert 'must2' in res['required_missing']


def test_forbidden_facts_found_and_not_found():
    case = ClinicalCase(id='f1', text='', symptoms=[], medications=[], required_facts=[], forbidden_facts=['bad_fact'], gold_summary={})
    pred_ok = Prediction(case_id='f1', summary_text='Nothing bad here.', medications=[])
    pred_bad = Prediction(case_id='f1', summary_text='This mentions bad_fact explicitly.', medications=[])
    ev = ForbiddenFactsEvaluator()
    r_ok = ev.evaluate(case, pred_ok)
    r_bad = ev.evaluate(case, pred_bad)
    assert r_ok['forbidden_score'] == pytest.approx(1.0)
    assert r_bad['forbidden_score'] == pytest.approx(0.0)
    assert 'bad_fact' in r_bad['forbidden_found']
