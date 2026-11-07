"""Tests for dataset.load_cases which reads JSONL input and returns ClinicalCase objects."""

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from medeval.dataset import load_cases
from medeval.models import ClinicalCase


def test_load_cases_jsonl(tmp_path):
    """Write a small JSONL file and ensure load_cases parses it into ClinicalCase objects."""
    lines = [
        {
            "id": "1",
            "text": "t1",
            "symptoms": ["s1"],
            "medications": ["m1"],
            "required_facts": [],
            "forbidden_facts": [],
            "gold_summary": {},
        },
        {
            "id": "2",
            "text": "t2",
            "symptoms": [],
            "medications": [],
            "required_facts": [],
            "forbidden_facts": [],
            "gold_summary": {},
        },
    ]
    p = tmp_path / "cases.jsonl"
    with open(str(p), "w", encoding="utf-8") as fh:
        for j in lines:
            fh.write(json.dumps(j) + "\n")
    cases = load_cases(str(p))
    assert len(cases) == 2
    assert cases[0].id == "1"
    assert isinstance(cases[0], ClinicalCase)
    assert cases[1].medications == []
