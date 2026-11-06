"""Statistical comparison utilities for A/B testing and model comparison.

This module provides tools for statistically rigorous comparison of model versions,
including confidence intervals, hypothesis testing, and effect size calculations.
"""

import logging
import math
from dataclasses import dataclass

logger = logging.getLogger("medeval.evaluation.statistics")


@dataclass
class ComparisonResult:
    """Result of a statistical comparison between two model versions."""

    metric_name: str
    baseline_mean: float
    candidate_mean: float
    difference: float
    percent_change: float
    confidence_interval_95: tuple[float, float]
    p_value: float
    is_significant: bool
    effect_size: float
    sample_size_baseline: int
    sample_size_candidate: int
    winner: str | None  # 'baseline', 'candidate', or None if no significant difference


class StatisticalComparator:
    """Utility for statistically comparing model versions.

    Provides methods for:
    - A/B testing with confidence intervals
    - Hypothesis testing (t-tests)
    - Effect size calculation (Cohen's d)
    - Multiple comparison correction (Bonferroni)

    Use this when:
    - Comparing model v1 vs v2
    - A/B testing in production
    - Deciding whether to deploy a new model
    - Regression testing (is new model worse?)

    Example:
        baseline_scores = [0.85, 0.87, 0.84, ...]  # Model v1
        candidate_scores = [0.88, 0.89, 0.87, ...]  # Model v2

        comparator = StatisticalComparator()
        result = comparator.compare_means(
            "f1_score",
            baseline_scores,
            candidate_scores
        )

        if result.is_significant and result.winner == 'candidate':
            print(f"Model v2 is {result.percent_change:.1f}% better (p={result.p_value:.3f})")
    """

    def __init__(self, significance_level: float = 0.05, min_effect_size: float = 0.0):
        """Initialize the statistical comparator.

        Args:
            significance_level: Alpha level for hypothesis tests (default 0.05 = 95% confidence)
            min_effect_size: Minimum Cohen's d to consider meaningful (default 0.0)
        """
        self.significance_level = significance_level
        self.min_effect_size = min_effect_size

    def compare_means(
        self, metric_name: str, baseline_values: list[float], candidate_values: list[float]
    ) -> ComparisonResult:
        """Compare means of two samples with statistical testing.

        Performs:
        1. Two-sample t-test
        2. 95% confidence interval for difference
        3. Cohen's d effect size
        4. Significance determination

        Args:
            metric_name: Name of the metric being compared
            baseline_values: Metric values for baseline model
            candidate_values: Metric values for candidate model

        Returns:
            ComparisonResult with full statistical analysis
        """
        logger.debug(
            f"Comparing {metric_name}: {len(baseline_values)} vs {len(candidate_values)} samples"
        )

        # Calculate basic statistics
        baseline_mean = self._mean(baseline_values)
        candidate_mean = self._mean(candidate_values)
        difference = candidate_mean - baseline_mean
        percent_change = (difference / baseline_mean * 100) if baseline_mean != 0 else 0.0

        # Calculate confidence interval for difference
        ci_95 = self._confidence_interval_difference(baseline_values, candidate_values)

        # Perform t-test
        t_stat, p_value = self._two_sample_t_test(baseline_values, candidate_values)

        # Calculate effect size
        effect_size = self._cohens_d(baseline_values, candidate_values)

        # Determine significance
        is_significant = (
            p_value < self.significance_level and abs(effect_size) >= self.min_effect_size
        )

        # Determine winner
        winner = None
        if is_significant:
            winner = "candidate" if difference > 0 else "baseline"

        logger.info(
            f"{metric_name}: {baseline_mean:.4f} → {candidate_mean:.4f} "
            f"({percent_change:+.2f}%), p={p_value:.4f}, d={effect_size:.3f}, "
            f"significant={is_significant}"
        )

        return ComparisonResult(
            metric_name=metric_name,
            baseline_mean=baseline_mean,
            candidate_mean=candidate_mean,
            difference=difference,
            percent_change=percent_change,
            confidence_interval_95=ci_95,
            p_value=p_value,
            is_significant=is_significant,
            effect_size=effect_size,
            sample_size_baseline=len(baseline_values),
            sample_size_candidate=len(candidate_values),
            winner=winner,
        )

    def compare_multiple_metrics(
        self, baseline_metrics: dict[str, list[float]], candidate_metrics: dict[str, list[float]]
    ) -> list[ComparisonResult]:
        """Compare multiple metrics with Bonferroni correction.

        When comparing multiple metrics, the chance of false positives increases.
        Bonferroni correction adjusts the significance level to account for this.

        Args:
            baseline_metrics: Dict mapping metric names to lists of values
            candidate_metrics: Dict mapping metric names to lists of values

        Returns:
            List of ComparisonResult objects, one per metric
        """
        num_comparisons = len(baseline_metrics)
        adjusted_alpha = self.significance_level / num_comparisons

        logger.info(
            f"Comparing {num_comparisons} metrics with Bonferroni correction: "
            f"α={self.significance_level:.3f} → {adjusted_alpha:.4f}"
        )

        results = []
        for metric_name in baseline_metrics.keys():
            if metric_name not in candidate_metrics:
                logger.warning(f"Metric {metric_name} not found in candidate, skipping")
                continue

            # Temporarily adjust significance level
            original_alpha = self.significance_level
            self.significance_level = adjusted_alpha

            result = self.compare_means(
                metric_name, baseline_metrics[metric_name], candidate_metrics[metric_name]
            )

            # Restore original significance level
            self.significance_level = original_alpha

            results.append(result)

        return results

    def _mean(self, values: list[float]) -> float:
        """Calculate mean."""
        return sum(values) / len(values) if values else 0.0

    def _variance(self, values: list[float]) -> float:
        """Calculate sample variance."""
        if len(values) < 2:
            return 0.0
        mean = self._mean(values)
        return sum((x - mean) ** 2 for x in values) / (len(values) - 1)

    def _standard_deviation(self, values: list[float]) -> float:
        """Calculate sample standard deviation."""
        return math.sqrt(self._variance(values))

    def _standard_error(self, values: list[float]) -> float:
        """Calculate standard error of the mean."""
        if not values:
            return 0.0
        return self._standard_deviation(values) / math.sqrt(len(values))

    def _confidence_interval_difference(
        self, baseline: list[float], candidate: list[float], confidence: float = 0.95
    ) -> tuple[float, float]:
        """Calculate confidence interval for difference in means.

        Returns (lower_bound, upper_bound) for the difference.
        """
        diff = self._mean(candidate) - self._mean(baseline)

        # Pooled standard error
        se_baseline = self._standard_error(baseline)
        se_candidate = self._standard_error(candidate)
        se_diff = math.sqrt(se_baseline**2 + se_candidate**2)

        # Use z=1.96 for 95% CI (approximation for large samples)
        # For small samples, should use t-distribution
        z_score = 1.96 if confidence == 0.95 else 2.576  # 99% CI

        margin_of_error = z_score * se_diff

        return (diff - margin_of_error, diff + margin_of_error)

    def _two_sample_t_test(
        self, baseline: list[float], candidate: list[float]
    ) -> tuple[float, float]:
        """Perform Welch's t-test (unequal variances).

        Returns (t_statistic, p_value).

        Note: This is a simplified implementation. For production, use scipy.stats.
        """
        mean_baseline = self._mean(baseline)
        mean_candidate = self._mean(candidate)
        var_baseline = self._variance(baseline)
        var_candidate = self._variance(candidate)
        n_baseline = len(baseline)
        n_candidate = len(candidate)

        if n_baseline < 2 or n_candidate < 2:
            return 0.0, 1.0  # Cannot compute

        # Welch's t-statistic
        numerator = mean_candidate - mean_baseline
        denominator = math.sqrt(var_baseline / n_baseline + var_candidate / n_candidate)

        if denominator == 0:
            return 0.0, 1.0

        t_stat = numerator / denominator

        # Degrees of freedom (Welch-Satterthwaite)
        numerator_df = (var_baseline / n_baseline + var_candidate / n_candidate) ** 2
        denominator_df = (var_baseline / n_baseline) ** 2 / (n_baseline - 1) + (
            var_candidate / n_candidate
        ) ** 2 / (n_candidate - 1)
        # Degrees of freedom (df) is computed for documentation of the Welch-Satterthwaite
        # approximation but is not used further since we approximate p-value via the normal
        # distribution below rather than the t-distribution.
        _ = numerator_df / denominator_df if denominator_df > 0 else 1

        # Approximate p-value using normal distribution (simplified)
        # For production, use scipy.stats.t.sf
        p_value = 2 * (1 - self._normal_cdf(abs(t_stat)))

        return t_stat, p_value

    def _cohens_d(self, baseline: list[float], candidate: list[float]) -> float:
        """Calculate Cohen's d effect size.

        Effect size interpretation:
        - |d| < 0.2: negligible
        - 0.2 <= |d| < 0.5: small
        - 0.5 <= |d| < 0.8: medium
        - |d| >= 0.8: large
        """
        mean_baseline = self._mean(baseline)
        mean_candidate = self._mean(candidate)
        std_baseline = self._standard_deviation(baseline)
        std_candidate = self._standard_deviation(candidate)

        # Pooled standard deviation
        n_baseline = len(baseline)
        n_candidate = len(candidate)
        pooled_std = math.sqrt(
            ((n_baseline - 1) * std_baseline**2 + (n_candidate - 1) * std_candidate**2)
            / (n_baseline + n_candidate - 2)
        )

        if pooled_std == 0:
            return 0.0

        return (mean_candidate - mean_baseline) / pooled_std

    def _normal_cdf(self, x: float) -> float:
        """Approximate cumulative distribution function for standard normal.

        This is a simple approximation. For production, use scipy.stats.norm.cdf.
        """
        # Using error function approximation
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def format_comparison_report(results: list[ComparisonResult]) -> str:
    """Format comparison results as a human-readable report.

    Args:
        results: List of ComparisonResult objects

    Returns:
        Formatted string report
    """
    lines = []
    lines.append("=" * 80)
    lines.append("STATISTICAL COMPARISON REPORT")
    lines.append("=" * 80)
    lines.append("")

    for result in results:
        lines.append(f"Metric: {result.metric_name}")
        lines.append(f"  Baseline:  {result.baseline_mean:.4f} (n={result.sample_size_baseline})")
        lines.append(f"  Candidate: {result.candidate_mean:.4f} (n={result.sample_size_candidate})")
        lines.append(f"  Difference: {result.difference:+.4f} ({result.percent_change:+.2f}%)")
        ci_low, ci_high = result.confidence_interval_95
        lines.append(f"  95% CI: [{ci_low:.4f}, {ci_high:.4f}]")
        lines.append(f"  p-value: {result.p_value:.4f}")
        lines.append(f"  Effect size (Cohen's d): {result.effect_size:.3f}")
        lines.append(f"  Significant: {result.is_significant}")
        if result.winner:
            lines.append(f"  Winner: {result.winner.upper()}")
        lines.append("")

    lines.append("=" * 80)

    return "\n".join(lines)
