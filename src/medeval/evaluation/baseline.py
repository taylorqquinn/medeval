"""Baseline loader for dataset-level thresholds."""

import json
from typing import Dict, Any

def load_baseline(path: str) -> Dict[str, Any]:
    """Load a baseline JSON file containing metric thresholds.

    The file is expected to be a JSON object mapping metric names to numeric thresholds.
    """
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)
