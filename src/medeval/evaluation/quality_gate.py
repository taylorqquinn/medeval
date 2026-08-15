"""Quality gate logic that determines pass/fail vs baseline."""

from typing import Dict, Any, Tuple, List

def evaluate_quality_gate(aggregated_metrics: Dict[str, Any], baseline: Dict[str, float]) -> Tuple[bool, List[str]]:
    """Compare aggregated metrics against baseline thresholds.

    Returns (passed, failures) where failures is a list of human-readable reasons.
    """
    failures = []
    for metric, threshold in baseline.items():
        actual = aggregated_metrics.get(metric)
        if actual is None:
            failures.append(f"Metric '{metric}' missing from results")
            continue
        try:
            actual_value = float(actual)
        except Exception:
            failures.append(f"Metric '{metric}' is non-numeric: {actual}")
            continue
        if actual_value < float(threshold):
            failures.append(f"Metric '{metric}' {actual_value:.3f} < threshold {threshold:.3f}")
    return (len(failures) == 0, failures)
