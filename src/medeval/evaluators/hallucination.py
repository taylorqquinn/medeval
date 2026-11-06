"""Hallucination and faithfulness detection evaluators.

This module provides evaluators for detecting hallucinations (unsupported claims)
and assessing faithfulness (grounding) in AI-generated text.
"""

import logging
import re
from typing import Any

from medeval.evaluators.base import Evaluator
from medeval.models import ClinicalCase, Prediction

logger = logging.getLogger("medeval.evaluators.hallucination")


class HallucinationDetectorEvaluator(Evaluator):
    """Evaluator that detects potential hallucinations in predictions.

    A hallucination occurs when the model generates information that is not
    supported by the input or ground truth. This evaluator performs basic
    hallucination detection by checking for:

    1. Forbidden facts appearing in output (explicitly disallowed content)
    2. Medication mentions not in ground truth (unsupported medications)
    3. Numeric claims that don't match source text

    For production use, consider integrating with:
    - Vectara's Hallucination Evaluation Model (HHEM)
    - SelfCheckGPT
    - RAGAs faithfulness metrics

    Returns:
        - hallucination_detected: bool (True if any hallucination found)
        - hallucination_score: float in [0, 1] (0 = clean, 1 = severe hallucination)
        - hallucination_types: list of detected hallucination types
        - forbidden_facts_found: list of forbidden facts that appeared
        - unsupported_medications: list of medications not in ground truth
    """

    def __init__(self, strict_mode: bool = False):
        """Initialize the hallucination detector.

        Args:
            strict_mode: If True, flag any deviation from ground truth as potential hallucination.
                        If False (default), only flag clear violations (forbidden facts, etc.)
        """
        super().__init__()
        self.strict_mode = strict_mode

    def evaluate(self, case: ClinicalCase, prediction: Prediction) -> dict[str, Any]:
        """Detect hallucinations in a prediction.

        Args:
            case: ClinicalCase with forbidden_facts and medications
            prediction: Prediction to check for hallucinations

        Returns:
            Dictionary with hallucination metrics and details
        """
        logger.debug(f"Detecting hallucinations for case {case.id}")

        hallucination_types = []
        forbidden_found = []
        unsupported_meds = []

        # Check for forbidden facts
        pred_text_lower = prediction.summary_text.lower()
        for forbidden in case.forbidden_facts or []:
            if forbidden.lower() in pred_text_lower:
                forbidden_found.append(forbidden)
                hallucination_types.append("forbidden_fact")
                logger.warning(f"Forbidden fact detected: '{forbidden}'")

        # Check for unsupported medications
        if self.strict_mode:
            gold_meds = set(m.lower().strip() for m in (case.medications or []))
            pred_meds = set(m.lower().strip() for m in (prediction.medications or []))
            unsupported = pred_meds - gold_meds
            if unsupported:
                unsupported_meds = list(unsupported)
                hallucination_types.append("unsupported_medication")
                logger.warning(f"Unsupported medications: {unsupported_meds}")

        # Check for numeric hallucinations (basic version)
        if case.source_text:
            numeric_hallucination = self._check_numeric_hallucination(
                case.source_text, prediction.summary_text
            )
            if numeric_hallucination:
                hallucination_types.append("numeric_hallucination")

        # Calculate hallucination score
        hallucination_detected = len(hallucination_types) > 0
        hallucination_score = self._calculate_hallucination_score(
            forbidden_found, unsupported_meds, hallucination_types
        )

        logger.debug(
            f"Hallucination detected: {hallucination_detected}, "
            f"Score: {hallucination_score:.3f}, "
            f"Types: {hallucination_types}"
        )

        return {
            "hallucination_detected": hallucination_detected,
            "hallucination_score": hallucination_score,
            "hallucination_types": hallucination_types,
            "forbidden_facts_found": forbidden_found,
            "unsupported_medications": unsupported_meds,
            "num_violations": len(forbidden_found) + len(unsupported_meds),
        }

    def _check_numeric_hallucination(self, source: str, prediction: str) -> bool:
        """Check if prediction contains numbers not in source.

        This is a simplified check - production systems should use more
        sophisticated fact verification.
        """
        # Extract numbers from both texts
        source_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", source))
        pred_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", prediction))

        # Check if prediction has numbers not in source
        unsupported_numbers = pred_numbers - source_numbers

        if unsupported_numbers:
            logger.debug(f"Numeric hallucination: numbers {unsupported_numbers} not in source")
            return True

        return False

    def _calculate_hallucination_score(
        self,
        forbidden_found: list[str],
        unsupported_meds: list[str],
        hallucination_types: list[str],
    ) -> float:
        """Calculate overall hallucination severity score.

        Score calculation:
        - Each forbidden fact: +0.3
        - Each unsupported medication: +0.2
        - Each other hallucination type: +0.1
        - Capped at 1.0
        """
        score = 0.0
        score += len(forbidden_found) * 0.3
        score += len(unsupported_meds) * 0.2

        other_types = [
            t for t in hallucination_types if t not in ["forbidden_fact", "unsupported_medication"]
        ]
        score += len(other_types) * 0.1

        return min(score, 1.0)


class FaithfulnessEvaluator(Evaluator):
    """Evaluator that checks if prediction is grounded in source text.

    Faithfulness (or grounding) measures whether the generated text is
    supported by the source context. This is critical for RAG systems
    where outputs should be derived from retrieved documents.

    This evaluator performs basic faithfulness checking:
    1. Sentence-level overlap with source text
    2. Entity coverage (entities in prediction appear in source)
    3. Claim verification (simplified version)

    For production RAG systems, consider:
    - RAGAs context_precision and context_recall
    - TruLens groundedness feedback
    - Custom fact-checking models

    Returns:
        - faithfulness_score: float in [0, 1] (1 = fully grounded)
        - grounded_sentences: int (sentences with source support)
        - total_sentences: int
        - ungrounded_claims: list of sentences lacking support
    """

    def __init__(self, min_overlap_threshold: float = 0.3):
        """Initialize the faithfulness evaluator.

        Args:
            min_overlap_threshold: Minimum word overlap ratio to consider
                                  a sentence grounded (0.0 to 1.0)
        """
        super().__init__()
        self.min_overlap_threshold = min_overlap_threshold

    def evaluate(self, case: ClinicalCase, prediction: Prediction) -> dict[str, Any]:
        """Evaluate faithfulness of prediction to source text.

        Args:
            case: ClinicalCase with source_text field
            prediction: Prediction to check for grounding

        Returns:
            Dictionary with faithfulness metrics
        """
        logger.debug(f"Evaluating faithfulness for case {case.id}")

        # Require source text for faithfulness evaluation
        if not case.source_text:
            logger.warning(f"Case {case.id} has no source_text, cannot evaluate faithfulness")
            return self._empty_result()

        source_text = case.source_text.lower()
        pred_text = prediction.summary_text

        # Split prediction into sentences
        sentences = self._split_sentences(pred_text)

        if not sentences:
            return self._empty_result()

        # Check grounding for each sentence
        grounded_count = 0
        ungrounded_claims = []

        for sentence in sentences:
            is_grounded = self._is_sentence_grounded(sentence, source_text)
            if is_grounded:
                grounded_count += 1
            else:
                ungrounded_claims.append(sentence)
                logger.debug(f"Ungrounded claim: '{sentence}'")

        # Calculate faithfulness score
        faithfulness_score = grounded_count / len(sentences) if sentences else 0.0

        logger.debug(
            f"Faithfulness score: {faithfulness_score:.3f} "
            f"({grounded_count}/{len(sentences)} sentences grounded)"
        )

        return {
            "faithfulness_score": faithfulness_score,
            "grounded_sentences": grounded_count,
            "total_sentences": len(sentences),
            "ungrounded_claims": ungrounded_claims[:3],  # Return first 3 for brevity
            "num_ungrounded": len(ungrounded_claims),
        }

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences (simplified)."""
        # Simple sentence splitting - production should use nltk or spacy
        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _is_sentence_grounded(self, sentence: str, source: str) -> bool:
        """Check if a sentence is grounded in source text.

        Uses simple word overlap heuristic. Production systems should use:
        - Semantic similarity (embeddings)
        - NLI models (entailment)
        - LLM-based verification
        """
        sentence_lower = sentence.lower()

        # Extract content words (skip common stop words)
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "is",
            "was",
            "are",
        }

        words = set(re.findall(r"\b\w+\b", sentence_lower))
        content_words = words - stop_words

        if not content_words:
            return True  # No content to verify

        # Check how many content words appear in source
        words_in_source = sum(1 for word in content_words if word in source)
        overlap_ratio = words_in_source / len(content_words)

        return overlap_ratio >= self.min_overlap_threshold

    def _empty_result(self) -> dict[str, Any]:
        """Return empty result when evaluation cannot be performed."""
        return {
            "faithfulness_score": None,
            "grounded_sentences": 0,
            "total_sentences": 0,
            "ungrounded_claims": [],
            "num_ungrounded": 0,
        }
