"""Unit tests for ClinicalAI.summarize.

These tests confirm the ClinicalAI constructs prompts correctly and returns a Prediction
with expected fields. Uses the deterministic LLMClient so outputs are stable.
"""

import os
import sys
import pytest
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from medeval.models import ClinicalCase
from medeval.application.clinical_ai import ClinicalAI
from medeval.application.llm_client import LLMClient


def test_summarize_with_symptoms_and_meds():
    """When symptoms and medications are provided, the summary should contain those sections."""
    llm = LLMClient()
    ai = ClinicalAI(llm_client=llm)
    case = ClinicalCase(
        id='c1',
        text='',
        symptoms=['chest pain'],
        medications=['Aspirin', 'Metformin'],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={}
    )
    pred = ai.summarize(case)
    assert pred.case_id == 'c1'
    assert ('Symptoms:' in pred.summary_text) or ('Medications:' in pred.summary_text)
    assert pred.medications == ['Aspirin', 'Metformin']
    assert 0.0 <= pred.confidence <= 1.0


def test_summarize_empty_case():
    """Empty input lists should yield an empty summary and confidence 0.0."""
    llm = LLMClient()
    ai = ClinicalAI(llm_client=llm)
    case = ClinicalCase(
        id='c2',
        text='',
        symptoms=[],
        medications=[],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={}
    )
    pred = ai.summarize(case)
    assert pred.summary_text == ''
    assert pred.medications == []
    assert pred.confidence == pytest.approx(0.0)
