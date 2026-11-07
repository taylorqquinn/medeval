"""Unit tests for statistical comparison utilities."""

import pytest

from medeval.evaluation.statistics import StatisticalComparator, format_comparison_report


def test_statistical_comparator_significant_improvement():
    """Model B is significantly better than Model A."""
    baseline = [0.80, 0.82, 0.81, 0.83, 0.79, 0.81, 0.82, 0.80, 0.81, 0.82]
    candidate = [0.88, 0.89, 0.87, 0.90, 0.88, 0.89, 0.88, 0.87, 0.89, 0.88]

    comparator = StatisticalComparator(significance_level=0.05)
    result = comparator.compare_means("f1_score", baseline, candidate)

    assert result.baseline_mean == pytest.approx(0.811, abs=0.01)
    assert result.candidate_mean == pytest.approx(0.883, abs=0.01)
    assert result.difference > 0.05  # Meaningful difference
    assert result.percent_change > 5.0  # >5% improvement
    assert result.is_significant is True
    assert result.winner == "candidate"
    assert result.effect_size > 0.5  # Medium to large effect


def test_statistical_comparator_no_significant_difference():
    """No significant difference between models."""
    baseline = [0.80, 0.82, 0.81, 0.83, 0.79]
    candidate = [0.81, 0.82, 0.80, 0.83, 0.80]

    comparator = StatisticalComparator(significance_level=0.05)
    result = comparator.compare_means("f1_score", baseline, candidate)

    assert abs(result.difference) < 0.05  # Very small difference
    assert result.is_significant is False
    assert result.winner is None  # No clear winner


def test_statistical_comparator_regression():
    """Model B is significantly worse (regression)."""
    baseline = [0.88, 0.89, 0.87, 0.90, 0.88]
    candidate = [0.75, 0.76, 0.74, 0.77, 0.75]

    comparator = StatisticalComparator(significance_level=0.05)
    result = comparator.compare_means("f1_score", baseline, candidate)

    assert result.difference < -0.10  # Large negative difference
    assert result.percent_change < -10.0  # >10% regression
    assert result.is_significant is True
    assert result.winner == "baseline"  # Baseline wins


def test_statistical_comparator_confidence_interval():
    """Confidence interval captures the true difference."""
    baseline = [0.80] * 20
    candidate = [0.85] * 20

    comparator = StatisticalComparator(significance_level=0.05)
    result = comparator.compare_means("f1_score", baseline, candidate)

    # Difference should be 0.05
    assert result.difference == pytest.approx(0.05, abs=0.001)

    # CI should contain the true difference (with floating point tolerance)
    ci_lower, ci_upper = result.confidence_interval_95
    assert ci_lower <= 0.051  # Allow floating point tolerance
    assert ci_upper >= 0.049

    # Since samples are identical within each group, CI should be tight
    assert (ci_upper - ci_lower) < 0.05


def test_statistical_comparator_small_sample():
    """Handle small sample sizes gracefully."""
    baseline = [0.80, 0.85]
    candidate = [0.82, 0.87]

    comparator = StatisticalComparator(significance_level=0.05)
    result = comparator.compare_means("f1_score", baseline, candidate)

    # Should still compute, but likely not significant due to small n
    assert result.sample_size_baseline == 2
    assert result.sample_size_candidate == 2
    assert result.p_value is not None


def test_statistical_comparator_multiple_metrics():
    """Compare multiple metrics with Bonferroni correction."""
    baseline_metrics = {
        "f1_score": [0.80, 0.82, 0.81, 0.83, 0.79],
        "precision": [0.85, 0.87, 0.86, 0.88, 0.84],
        "recall": [0.75, 0.77, 0.76, 0.78, 0.74],
    }

    candidate_metrics = {
        "f1_score": [0.88, 0.89, 0.87, 0.90, 0.88],
        "precision": [0.90, 0.91, 0.89, 0.92, 0.90],
        "recall": [0.85, 0.87, 0.86, 0.88, 0.85],
    }

    comparator = StatisticalComparator(significance_level=0.05)
    results = comparator.compare_multiple_metrics(baseline_metrics, candidate_metrics)

    assert len(results) == 3

    # All metrics should show improvement
    for result in results:
        assert result.difference > 0
        assert result.candidate_mean > result.baseline_mean


def test_statistical_comparator_min_effect_size():
    """Require minimum effect size for significance."""
    # Small but "significant" difference (p < 0.05)
    baseline = [0.800] * 100  # Large sample
    candidate = [0.805] * 100  # Tiny improvement

    # Without min effect size requirement
    comparator1 = StatisticalComparator(significance_level=0.05, min_effect_size=0.0)
    _ = comparator1.compare_means("f1_score", baseline, candidate)

    # With min effect size requirement (require medium effect)
    comparator2 = StatisticalComparator(
        significance_level=0.05, min_effect_size=0.5  # Medium effect
    )
    result2 = comparator2.compare_means("f1_score", baseline, candidate)

    # First might be "significant" (p < 0.05 due to large sample)
    # Second should not be significant (effect size too small)
    assert result2.effect_size < 0.5
    assert result2.is_significant is False


def test_format_comparison_report():
    """Format comparison results as readable report."""
    baseline = [0.80, 0.82, 0.81]
    candidate = [0.88, 0.89, 0.87]

    comparator = StatisticalComparator()
    result = comparator.compare_means("f1_score", baseline, candidate)

    report = format_comparison_report([result])

    # Check report contains key information
    assert "STATISTICAL COMPARISON REPORT" in report
    assert "f1_score" in report
    assert "Baseline:" in report
    assert "Candidate:" in report
    assert "p-value:" in report
    assert "Effect size" in report
    assert "Winner:" in report


def test_statistical_comparator_identical_distributions():
    """Handle identical distributions (no difference)."""
    baseline = [0.85, 0.85, 0.85, 0.85, 0.85]
    candidate = [0.85, 0.85, 0.85, 0.85, 0.85]

    comparator = StatisticalComparator()
    result = comparator.compare_means("f1_score", baseline, candidate)

    assert result.difference == 0.0
    assert result.percent_change == 0.0
    assert result.effect_size == 0.0
    assert result.is_significant is False
    assert result.winner is None
