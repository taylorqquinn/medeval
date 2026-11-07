"""Data models for MedEval."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RetrievedDocument:
    """A document retrieved by a RAG system."""

    doc_id: str
    text: str
    score: float
    rank: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ClinicalCase:
    """A synthetic clinical case used as input to the AI."""

    id: str
    text: str
    symptoms: list[str]
    medications: list[str]
    required_facts: list[str]
    forbidden_facts: list[str]
    gold_summary: dict[str, Any]
    # RAG-specific fields
    relevant_doc_ids: list[str] | None = None  # Ground truth relevant docs
    source_text: str | None = None  # Source text for faithfulness checking
    # Adversarial testing fields
    is_adversarial: bool = False
    adversarial_type: str | None = None  # e.g., "prompt_injection", "jailbreak"


@dataclass
class Prediction:
    """Structured prediction returned by the clinical AI under test."""

    case_id: str
    summary_text: str
    medications: list[str]
    confidence: float | None = None
    # RAG-specific fields
    retrieved_docs: list[RetrievedDocument] | None = None
    # Performance fields
    latency_ms: float | None = None
    cost_usd: float | None = None
    tokens_used: int | None = None
    # Safety fields
    safety_flags: list[str] | None = None
    detected_attacks: list[str] | None = None
