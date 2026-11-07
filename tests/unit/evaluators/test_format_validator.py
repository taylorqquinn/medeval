"""Unit tests for the FormatValidator.

These tests document expected behavior for presence/absence of a 'Medications:'
section, the effect of the require_med_section flag, and length-based failures.
"""

import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from medeval.evaluators.format_validator import FormatValidator
from medeval.models import ClinicalCase, Prediction


def test_format_validator_missing_and_present():
    """Missing 'Medications:' should produce an error; present should pass."""
    case = ClinicalCase(
        id="f1",
        text="",
        symptoms=[],
        medications=[],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
    )
    pred1 = Prediction(case_id="f1", summary_text="This has no meds section.", medications=[])
    pred2 = Prediction(case_id="f1", summary_text="Medications: aspirin.", medications=["aspirin"])
    ev = FormatValidator()
    r1 = ev.evaluate(case, pred1)
    r2 = ev.evaluate(case, pred2)
    assert r1["format_score"] == pytest.approx(0.0)
    assert "missing_medications_section" in r1["format_errors"]
    assert r2["format_score"] == pytest.approx(1.0)


def test_format_validator_length_and_flags():
    """Long summaries should be flagged and require_med_section flag is honored."""
    case = ClinicalCase(
        id="f2",
        text="",
        symptoms=[],
        medications=[],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
    )
    long_text = "a" * 200
    ev = FormatValidator(require_med_section=False, max_length=50)
    pred = Prediction(case_id="f2", summary_text=long_text, medications=[])
    r = ev.evaluate(case, pred)
    assert r["format_score"] == pytest.approx(0.0)
    assert "summary_too_long" in r["format_errors"]

    ev2 = FormatValidator(require_med_section=False, max_length=1000)
    pred2 = Prediction(case_id="f2", summary_text="No meds here", medications=[])
    r2 = ev2.evaluate(case, pred2)
    assert r2["format_score"] == pytest.approx(1.0)
