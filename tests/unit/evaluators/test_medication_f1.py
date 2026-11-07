"""Unit tests for medication F1 evaluator.

These tests serve both as verification and as documentation for the expected
behavior of the MedicationF1Evaluator. Each test includes a short docstring
explaining the scenario, the inputs and the expected outcome.
"""

import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from medeval.evaluators.medication_f1 import MedicationF1Evaluator
from medeval.models import ClinicalCase, Prediction


def test_medication_f1_exact_match():
    """When one predicted medication matches one of the gold medications.

    Gold: [Aspirin, Metformin]
    Pred: [aspirin]

    Expectation:
      - precision = 1.0 (all predicted meds are correct)
      - recall = 0.5 (1 of 2 gold meds recovered)
      - f1 = 2/3
    """
    case = ClinicalCase(
        id="t1",
        text="",
        symptoms=[],
        medications=["Aspirin", "Metformin"],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
    )
    pred = Prediction(case_id="t1", summary_text="", medications=["aspirin"])
    ev = MedicationF1Evaluator()
    res = ev.evaluate(case, pred)
    assert res["med_precision"] == pytest.approx(1.0)
    assert res["med_recall"] == pytest.approx(0.5)
    assert res["med_f1"] == pytest.approx(2 / 3)


def test_medication_f1_no_predictions():
    """When the prediction provides no medications but gold has medications.

    According to the evaluator logic:
      - precision = 0.0 (no predicted items)
      - recall = 0.0 (no gold recovered)
      - f1 = 0.0
    """
    case = ClinicalCase(
        id="t2",
        text="",
        symptoms=[],
        medications=["Aspirin"],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
    )
    pred = Prediction(case_id="t2", summary_text="", medications=[])
    ev = MedicationF1Evaluator()
    res = ev.evaluate(case, pred)
    assert res["med_precision"] == pytest.approx(0.0)
    assert res["med_recall"] == pytest.approx(0.0)
    assert res["med_f1"] == pytest.approx(0.0)


def test_medication_f1_both_empty():
    """If both gold and predicted medication lists are empty the evaluator treats
    this as a trivial perfect match (precision=recall=f1=1.0).
    """
    case = ClinicalCase(
        id="t3",
        text="",
        symptoms=[],
        medications=[],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
    )
    pred = Prediction(case_id="t3", summary_text="", medications=[])
    ev = MedicationF1Evaluator()
    res = ev.evaluate(case, pred)
    assert res["med_precision"] == pytest.approx(1.0)
    assert res["med_recall"] == pytest.approx(1.0)
    assert res["med_f1"] == pytest.approx(1.0)
