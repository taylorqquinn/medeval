"""Tests for the CalibrationEvaluator which exposes per-case confidence and correctness."""

import os
import sys
import pytest
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from medeval.models import ClinicalCase, Prediction
from medeval.evaluators.calibration import CalibrationEvaluator
from medeval.application.llm_client import LLMClient


def test_calibration_evaluator_judge_and_confidence():
    """CalibrationEvaluator should return confidence, is_correct, and judge_score."""
    llm = LLMClient()
    ev = CalibrationEvaluator(llm_client=llm, threshold=0.5)
    case = ClinicalCase(id='c1', text='', symptoms=[], medications=[], required_facts=[], forbidden_facts=[], gold_summary={'summary_text':'a b c'})
    pred = Prediction(case_id='c1', summary_text='a x y', medications=[], confidence=0.9)
    res = ev.evaluate(case, pred)
    assert 'confidence' in res and 'is_correct' in res and 'judge_score' in res
    assert res['confidence'] == pytest.approx(0.9)
    assert 0.0 <= res['judge_score'] <= 1.0
    assert res['is_correct'] == pytest.approx(0.0)


def test_calibration_default_confidence_when_missing():
    """If prediction.confidence missing, default 0.5 is used."""
    llm = LLMClient()
    ev = CalibrationEvaluator(llm_client=llm, threshold=0.5)
    case = ClinicalCase(id='c2', text='', symptoms=[], medications=[], required_facts=[], forbidden_facts=[], gold_summary={'summary_text':''})
    pred = Prediction(case_id='c2', summary_text='', medications=[])
    res = ev.evaluate(case, pred)
    assert res['confidence'] == pytest.approx(0.5)
