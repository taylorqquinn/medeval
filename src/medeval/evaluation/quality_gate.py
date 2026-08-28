"""Quality gate logic that determines pass/fail vs baseline."""

from typing import Dict, Any, Tuple, List

def evaluate_quality_gate(aggregated_metrics: Dict[str, Any], baseline: Dict[str, float]) -> Tuple[bool, List[str]]:
    """Compare aggregated metrics against baseline thresholds.

    For each metric in baseline, the corresponding value is looked up in aggregated_metrics
    and converted to float. If a metric is missing or non-numeric, a human-readable failure
    message is returned.

    Returns:
        (passed, failures)
          - passed: True if all threshold checks succeeded, otherwise False
          - failures: list of strings describing missing or failing metrics

    Example:
        aggregated = {'med_f1': 0.8}
        baseline = {'med_f1': 0.75}
        => (True, [])
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
            failures.append(f"Metric '{metric}' {actual_value:.3f} < threshold {float(threshold):.3f}")
    return (len(failures) == 0, failures)
