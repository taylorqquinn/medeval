import os
import sys
import pytest
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from medeval.evaluation.metrics import aggregate


def test_calibration_ece_perfect():
    # perfect calibration: confidences 1.0/0.0 with matching correctness
    per_case = [
        {'confidence': 1.0, 'is_correct': 1.0},
        {'confidence': 0.0, 'is_correct': 0.0}
    ]
    agg = aggregate(per_case)
    assert 'calibration_ece' in agg
    assert agg['calibration_ece'] == pytest.approx(0.0)
