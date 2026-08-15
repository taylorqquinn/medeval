"""Console report helper for MedEval."""

def print_report(aggregated_metrics, passed: bool, failures):
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
