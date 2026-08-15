import os
import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from medeval.evaluation.runner import run


def test_runner_smoke():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    dataset = os.path.join(root, 'datasets', 'clinical_cases.jsonl')
    baseline = os.path.join(root, 'baselines', 'production.json')
    res = run(dataset, baseline)
    assert 'aggregated' in res
    assert isinstance(res['aggregated'], dict)
    assert 'passed' in res
