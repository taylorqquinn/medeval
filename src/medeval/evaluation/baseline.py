"""Baseline loader for dataset-level thresholds."""

import json
from typing import Dict, Any

def load_baseline(path: str) -> Dict[str, Any]:
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)
