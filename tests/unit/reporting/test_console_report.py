"""Simple test for the console reporting helper.

Captures stdout and verifies the report contains key sections and the quality gate output.
"""

import os
import sys
import pytest
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from medeval.reporting.console_report import print_report


def test_print_report_captures_output(capsys):
    aggregated = {'med_f1': 0.9, 'llm_judge_score': 0.8}
    print_report(aggregated, True, [])
    captured = capsys.readouterr()
    assert 'MedEval report' in captured.out
    assert 'med_f1' in captured.out
    assert 'Quality gate: PASS' in captured.out
