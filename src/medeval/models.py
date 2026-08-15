"""Data models for MedEval."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class ClinicalCase:
    """A synthetic clinical case used as input to the AI."""
    id: str
    text: str
    symptoms: List[str]
    medications: List[str]
    required_facts: List[str]
    forbidden_facts: List[str]
    gold_summary: Dict[str, Any]

@dataclass
class Prediction:
    """Structured prediction returned by the clinical AI under test."""
    case_id: str
    summary_text: str
    medications: List[str]
    confidence: Optional[float] = None
