"""Dataset loading utilities."""

import json
from typing import List
from medeval.models import ClinicalCase

def load_cases(path: str) -> List[ClinicalCase]:
    """Load clinical cases from a JSONL file."""
    cases: List[ClinicalCase] = []
    with open(path, 'r', encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            j = json.loads(line)
            cases.append(ClinicalCase(
                id=str(j.get("id","")),
                text=j.get("text",""),
                symptoms=j.get("symptoms",[]),
                medications=j.get("medications",[]),
                required_facts=j.get("required_facts",[]),
                forbidden_facts=j.get("forbidden_facts",[]),
                gold_summary=j.get("gold_summary",{})
            ))
    return cases
