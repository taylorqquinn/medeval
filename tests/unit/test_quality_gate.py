import os
import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from medeval.evaluation.quality_gate import evaluate_quality_gate


def test_quality_gate_pass_and_fail():
    aggregated = {'med_f1':0.8, 'llm_judge_score':0.9, 'required_facts_score':1.0, 'forbidden_score':1.0}
    baseline = {'med_f1':0.75, 'llm_judge_score':0.5}
    passed, failures = evaluate_quality_gate(aggregated, baseline)
    assert passed
    assert failures == []

    baseline2 = {'med_f1':0.9}
    passed2, failures2 = evaluate_quality_gate(aggregated, baseline2)
    assert not passed2
    assert len(failures2) == 1
