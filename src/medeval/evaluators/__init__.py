"""MedEval Evaluators - Core evaluation metrics for medical AI systems."""

from medeval.evaluators.base import Evaluator, discover_evaluators, list_available_evaluators
from medeval.evaluators.calibration import CalibrationEvaluator
from medeval.evaluators.entity_extraction import EntityExtractionEvaluator
from medeval.evaluators.forbidden_facts import ForbiddenFactsEvaluator
from medeval.evaluators.format_validator import FormatValidator

# Hallucination & faithfulness
from medeval.evaluators.hallucination import FaithfulnessEvaluator, HallucinationDetectorEvaluator
from medeval.evaluators.llm_judge import LLMJudgeEvaluator
from medeval.evaluators.medication_f1 import MedicationF1Evaluator

# Performance & reliability
from medeval.evaluators.performance import PerformanceEvaluator, ReliabilityEvaluator
from medeval.evaluators.required_facts import RequiredFactsEvaluator

# RAG evaluators
from medeval.evaluators.retrieval import RetrievalEvaluator

# Safety & adversarial
from medeval.evaluators.safety import (
    AdversarialRobustnessEvaluator,
    PromptInjectionDetectorEvaluator,
    SafetyGuardEvaluator,
)

__all__ = [
    # Base
    "Evaluator",
    "discover_evaluators",
    "list_available_evaluators",
    # Concrete evaluators
    "MedicationF1Evaluator",
    "RequiredFactsEvaluator",
    "ForbiddenFactsEvaluator",
    "EntityExtractionEvaluator",
    "FormatValidator",
    "CalibrationEvaluator",
    "LLMJudgeEvaluator",
    # RAG evaluators
    "RetrievalEvaluator",
    # Hallucination & faithfulness
    "HallucinationDetectorEvaluator",
    "FaithfulnessEvaluator",
    # Safety & adversarial
    "PromptInjectionDetectorEvaluator",
    "AdversarialRobustnessEvaluator",
    "SafetyGuardEvaluator",
    # Performance & reliability
    "PerformanceEvaluator",
    "ReliabilityEvaluator",
]
