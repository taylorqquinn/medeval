"""Console report helper for MedEval."""

def print_report(aggregated_metrics, passed: bool, failures):
    """Print a human-readable report to stdout.

    This helper prints aggregated metrics (key: value lines), a separator, the
    quality gate result (PASS/FAIL) and any failure messages. It is intentionally
    small and suitable for demonstration or simple CI logs.
    """
    print("MedEval report")
    print("=" * 40)
    for k, v in aggregated_metrics.items():
        print(f"{k}: {v}")
    print("-" * 40)
    print("Quality gate:", "PASS" if passed else "FAIL")
    if failures:
        print("Failures:")
        for f in failures:
            print(" -", f)
