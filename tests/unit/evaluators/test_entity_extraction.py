"""Unit tests for the EntityExtractionEvaluator.

These tests document the heuristic parsing behavior for 'Symptoms:' and 'Medications:'
sections and confirm the metrics computed for extraction tasks.
"""

import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from medeval.evaluators.entity_extraction import EntityExtractionEvaluator
from medeval.models import ClinicalCase, Prediction


def test_entity_extraction_basic():
    """Basic extraction from well-formed 'Symptoms:' and 'Medications:' sections."""
    case = ClinicalCase(
        id="e1",
        text="",
        symptoms=["chest pain"],
        medications=["aspirin", "metformin"],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
    )
    pred = Prediction(
        case_id="e1",
        summary_text="Symptoms: chest pain. Medications: Aspirin, Metformin.",
        medications=["aspirin", "metformin"],
    )
    ev = EntityExtractionEvaluator()
    res = ev.evaluate(case, pred)
    assert res["entity_med_precision"] == pytest.approx(1.0)
    assert res["entity_med_recall"] == pytest.approx(1.0)
    assert res["entity_symptom_precision"] == pytest.approx(1.0)
    assert res["entity_symptom_recall"] == pytest.approx(1.0)


def test_entity_extraction_punctuation_and_missing_sections():
    """Ensure punctuation is tolerated and missing sections handled deterministically."""
    case = ClinicalCase(
        id="e2",
        text="",
        symptoms=["fever"],
        medications=["ibuprofen"],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
    )
    pred_missing = Prediction(
        case_id="e2", summary_text="No structured sections here.", medications=[]
    )
    ev = EntityExtractionEvaluator()
    r_missing = ev.evaluate(case, pred_missing)
    assert r_missing["entity_med_precision"] == pytest.approx(0.0)
    assert r_missing["entity_med_recall"] == pytest.approx(0.0)

    pred_punc = Prediction(
        case_id="e2", summary_text="Medications: Ibuprofen.", medications=["ibuprofen"]
    )
    r_punc = ev.evaluate(case, pred_punc)
    assert r_punc["entity_med_precision"] == pytest.approx(1.0)
    assert r_punc["entity_med_recall"] == pytest.approx(1.0)
