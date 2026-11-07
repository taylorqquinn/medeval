"""Unit tests for performance and reliability evaluators."""

from medeval.evaluators.performance import PerformanceEvaluator, ReliabilityEvaluator
from medeval.models import ClinicalCase, Prediction


def test_performance_within_sla():
    """Performance metrics within SLA thresholds."""
    case = ClinicalCase(
        id="test1",
        text="",
        symptoms=[],
        medications=[],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
    )

    prediction = Prediction(
        case_id="test1",
        summary_text="Good response",
        medications=[],
        latency_ms=450.0,
        cost_usd=0.003,
        tokens_used=1200,
    )

    evaluator = PerformanceEvaluator(latency_sla_ms=500.0, cost_sla_usd=0.005)
    result = evaluator.evaluate(case, prediction)

    assert result["latency_ms"] == 450.0
    assert result["cost_usd"] == 0.003
    assert result["tokens_used"] == 1200
    assert result["passed_latency_sla"] is True
    assert result["passed_cost_sla"] is True


def test_performance_violate_latency_sla():
    """Latency exceeds SLA threshold."""
    case = ClinicalCase(
        id="test2",
        text="",
        symptoms=[],
        medications=[],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
    )

    prediction = Prediction(
        case_id="test2",
        summary_text="Slow response",
        medications=[],
        latency_ms=750.0,  # Exceeds 500ms SLA
        cost_usd=0.002,
        tokens_used=1500,
    )

    evaluator = PerformanceEvaluator(latency_sla_ms=500.0, cost_sla_usd=0.005)
    result = evaluator.evaluate(case, prediction)

    assert result["passed_latency_sla"] is False  # Violated SLA
    assert result["passed_cost_sla"] is True


def test_performance_violate_cost_sla():
    """Cost exceeds SLA threshold."""
    case = ClinicalCase(
        id="test3",
        text="",
        symptoms=[],
        medications=[],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
    )

    prediction = Prediction(
        case_id="test3",
        summary_text="Expensive response",
        medications=[],
        latency_ms=300.0,
        cost_usd=0.008,  # Exceeds 0.005 SLA
        tokens_used=5000,
    )

    evaluator = PerformanceEvaluator(latency_sla_ms=500.0, cost_sla_usd=0.005)
    result = evaluator.evaluate(case, prediction)

    assert result["passed_latency_sla"] is True
    assert result["passed_cost_sla"] is False  # Violated SLA


def test_performance_no_metrics():
    """Handle missing performance metrics gracefully."""
    case = ClinicalCase(
        id="test4",
        text="",
        symptoms=[],
        medications=[],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
    )

    prediction = Prediction(
        case_id="test4",
        summary_text="Response without metrics",
        medications=[],
        # No latency_ms, cost_usd, tokens_used
    )

    evaluator = PerformanceEvaluator(latency_sla_ms=500.0)
    result = evaluator.evaluate(case, prediction)

    assert result["latency_ms"] is None
    assert result["cost_usd"] is None
    assert result["tokens_used"] is None
    assert result["passed_latency_sla"] is None  # Can't check without data


def test_reliability_successful_prediction():
    """Prediction succeeds without errors."""
    case = ClinicalCase(
        id="test5",
        text="",
        symptoms=[],
        medications=[],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
    )

    prediction = Prediction(
        case_id="test5",
        summary_text="Patient presents with cardiac symptoms requiring immediate evaluation.",
        medications=[],
        latency_ms=400.0,
    )

    evaluator = ReliabilityEvaluator(timeout_threshold_ms=5000)
    result = evaluator.evaluate(case, prediction)

    assert result["prediction_succeeded"] is True
    assert result["is_error"] is False
    assert result["is_timeout"] is False
    assert result["error_type"] is None
    assert result["availability"] == 1.0


def test_reliability_error_prediction():
    """Prediction contains error message."""
    case = ClinicalCase(
        id="test6",
        text="",
        symptoms=[],
        medications=[],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
    )

    prediction = Prediction(
        case_id="test6", summary_text="Error: Internal service error occurred", medications=[]
    )

    evaluator = ReliabilityEvaluator()
    result = evaluator.evaluate(case, prediction)

    assert result["prediction_succeeded"] is False
    assert result["is_error"] is True
    assert result["error_type"] is not None
    assert result["availability"] == 0.0


def test_reliability_timeout():
    """Prediction exceeds timeout threshold."""
    case = ClinicalCase(
        id="test7",
        text="",
        symptoms=[],
        medications=[],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
    )

    prediction = Prediction(
        case_id="test7",
        summary_text="Valid response but took too long",
        medications=[],
        latency_ms=6000.0,  # Exceeds 5000ms threshold
    )

    evaluator = ReliabilityEvaluator(timeout_threshold_ms=5000)
    result = evaluator.evaluate(case, prediction)

    assert result["prediction_succeeded"] is False  # Failed due to timeout
    assert result["is_timeout"] is True
    assert result["availability"] == 0.0


def test_reliability_empty_output():
    """Empty or very short output is considered an error."""
    case = ClinicalCase(
        id="test8",
        text="",
        symptoms=[],
        medications=[],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
    )

    prediction = Prediction(case_id="test8", summary_text="", medications=[])  # Empty output

    evaluator = ReliabilityEvaluator()
    result = evaluator.evaluate(case, prediction)

    assert result["prediction_succeeded"] is False
    assert result["is_error"] is True
