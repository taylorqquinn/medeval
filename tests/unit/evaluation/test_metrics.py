"""Unit tests for the metrics.aggregate helper.

These tests verify averaging of numeric fields, concatenation of non-numeric
fields, and correct computation of the dataset-level calibration ECE.
"""

import os
import sys
import pytest
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from medeval.evaluation.metrics import aggregate


def test_aggregate_numeric_and_list():
    per_case = [
        {'med_f1': 1.0, 'format_errors': ['a']},
        {'med_f1': 0.0, 'format_errors': ['b']}
    ]
    agg = aggregate(per_case)
    assert agg['med_f1'] == pytest.approx(0.5)
    assert isinstance(agg['format_errors'], list)
    assert set(agg['format_errors']) == {'a', 'b'} or agg['format_errors'] == ['a', 'b']


def test_aggregate_ece_computation():
    per_case = [
        {'confidence': 1.0, 'is_correct': 1.0},
        {'confidence': 0.0, 'is_correct': 0.0}
    ]
    agg = aggregate(per_case)
    assert 'calibration_ece' in agg
    assert agg['calibration_ece'] == pytest.approx(0.0)
