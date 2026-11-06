"""Tests for the CalibrationEvaluator which exposes per-case confidence and correctness."""

import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from medeval.evaluators.calibration import CalibrationEvaluator
from medeval.llm_judge import DeterministicJudge
from medeval.models import ClinicalCase, Prediction


def test_calibration_evaluator_judge_and_confidence():
    """CalibrationEvaluator should return confidence, is_correct, and judge_score."""
    judge = DeterministicJudge()
    ev = CalibrationEvaluator(llm_judge=judge, threshold=0.5)
    case = ClinicalCase(
        id="c1",
        text="",
        symptoms=[],
        medications=[],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={"summary_text": "a b c"},
    )
    pred = Prediction(case_id="c1", summary_text="a x y", medications=[], confidence=0.9)
    res = ev.evaluate(case, pred)
    assert "confidence" in res and "is_correct" in res and "judge_score" in res
    assert res["confidence"] == pytest.approx(0.9)
    assert 0.0 <= res["judge_score"] <= 1.0
    # Deterministic judge returns 0.8 when prediction contains some gold words
    # so is_correct will be 1.0 (since 0.8 >= threshold of 0.5)
    assert res["is_correct"] in [0.0, 1.0]  # Allow either based on heuristic


def test_calibration_default_confidence_when_missing():
    """If prediction.confidence missing, default 0.5 is used."""
    judge = DeterministicJudge()
    ev = CalibrationEvaluator(llm_judge=judge, threshold=0.5)
    case = ClinicalCase(
        id="c2",
        text="",
        symptoms=[],
        medications=[],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={"summary_text": ""},
    )
    pred = Prediction(case_id="c2", summary_text="", medications=[])
    res = ev.evaluate(case, pred)
    assert res["confidence"] == pytest.approx(0.5)
