"""Unit tests for hallucination detection evaluators."""

from medeval.evaluators.hallucination import FaithfulnessEvaluator, HallucinationDetectorEvaluator
from medeval.models import ClinicalCase, Prediction


def test_hallucination_forbidden_facts_detected():
    """Detect forbidden facts appearing in output."""
    case = ClinicalCase(
        id="test1",
        text="Patient with chest pain",
        symptoms=["chest pain"],
        medications=["aspirin"],
        required_facts=[],
        forbidden_facts=["definitely cancer", "terminal"],
        gold_summary={},
        source_text="Patient reports chest pain for 2 hours",
    )

    prediction = Prediction(
        case_id="test1",
        summary_text="Patient definitely has cancer and condition is terminal",
        medications=["aspirin"],
    )

    evaluator = HallucinationDetectorEvaluator(strict_mode=False)
    result = evaluator.evaluate(case, prediction)

    assert result["hallucination_detected"] is True
    assert "forbidden_fact" in result["hallucination_types"]
    assert len(result["forbidden_facts_found"]) >= 1  # At least one forbidden fact found
    assert result["hallucination_score"] > 0.2  # Significant hallucination


def test_hallucination_unsupported_medications():
    """Detect medications not in ground truth (strict mode)."""
    case = ClinicalCase(
        id="test2",
        text="Patient with diabetes",
        symptoms=["high blood sugar"],
        medications=["metformin"],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
    )

    prediction = Prediction(
        case_id="test2",
        summary_text="Prescribed metformin and insulin",
        medications=["metformin", "insulin"],  # insulin not in ground truth
    )

    evaluator = HallucinationDetectorEvaluator(strict_mode=True)
    result = evaluator.evaluate(case, prediction)

    assert result["hallucination_detected"] is True
    assert "unsupported_medication" in result["hallucination_types"]
    assert "insulin" in result["unsupported_medications"]


def test_hallucination_clean_output():
    """No hallucinations detected in clean output."""
    case = ClinicalCase(
        id="test3",
        text="Patient stable",
        symptoms=[],
        medications=["aspirin"],
        required_facts=[],
        forbidden_facts=["fatal", "dying"],
        gold_summary={},
    )

    prediction = Prediction(
        case_id="test3",
        summary_text="Patient is stable and responding to aspirin therapy",
        medications=["aspirin"],
    )

    evaluator = HallucinationDetectorEvaluator(strict_mode=True)
    result = evaluator.evaluate(case, prediction)

    assert result["hallucination_detected"] is False
    assert result["hallucination_score"] == 0.0
    assert len(result["hallucination_types"]) == 0


def test_faithfulness_fully_grounded():
    """All claims are grounded in source text."""
    case = ClinicalCase(
        id="test4",
        text="",
        symptoms=[],
        medications=[],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
        source_text=(
            "Patient reports chest pain for 2 hours. "
            "No history of heart disease. Vital signs stable."
        ),
    )

    prediction = Prediction(
        case_id="test4",
        summary_text="Patient has chest pain lasting 2 hours. Vital signs are stable.",
        medications=[],
    )

    evaluator = FaithfulnessEvaluator(min_overlap_threshold=0.3)
    result = evaluator.evaluate(case, prediction)

    assert result["faithfulness_score"] >= 0.8  # Mostly grounded
    assert result["grounded_sentences"] >= 1
    assert len(result["ungrounded_claims"]) <= 1  # Few or no ungrounded claims


def test_faithfulness_ungrounded_claims():
    """Detect claims not supported by source."""
    case = ClinicalCase(
        id="test5",
        text="",
        symptoms=[],
        medications=[],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
        source_text="Patient reports mild headache today.",
    )

    prediction = Prediction(
        case_id="test5",
        summary_text="Patient has severe migraine for 3 weeks. History of stroke.",
        medications=[],
    )

    evaluator = FaithfulnessEvaluator(min_overlap_threshold=0.3)
    result = evaluator.evaluate(case, prediction)

    assert result["faithfulness_score"] < 0.5  # Mostly ungrounded
    assert result["num_ungrounded"] >= 1


def test_faithfulness_no_source_text():
    """Edge case: No source text provided."""
    case = ClinicalCase(
        id="test6",
        text="",
        symptoms=[],
        medications=[],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
        source_text=None,
    )

    prediction = Prediction(case_id="test6", summary_text="Some prediction", medications=[])

    evaluator = FaithfulnessEvaluator()
    result = evaluator.evaluate(case, prediction)

    # Should return empty result when no source text
    assert result["faithfulness_score"] is None
    assert result["grounded_sentences"] == 0


def test_hallucination_numeric_hallucination():
    """Detect numbers in prediction not present in source."""
    case = ClinicalCase(
        id="test7",
        text="",
        symptoms=[],
        medications=[],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
        source_text="Patient temperature is 37.2 degrees.",
    )

    prediction = Prediction(
        case_id="test7",
        summary_text="Patient has fever of 39.5 degrees for 3 days.",
        medications=[],
    )

    evaluator = HallucinationDetectorEvaluator(strict_mode=False)
    result = evaluator.evaluate(case, prediction)

    # Should detect numeric hallucination (39.5 and 3 not in source)
    assert result["hallucination_detected"] is True
    assert "numeric_hallucination" in result["hallucination_types"]
