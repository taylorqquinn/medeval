"""Software-level integration test that runs the full evaluation pipeline.

This test exercises the complete medeval application from dataset loading through
evaluation and quality gate checking. It can be run directly to verify the system
works end-to-end without needing command-line arguments.

Usage:
    python tests/software/test_full_pipeline.py

The test uses the sample datasets and baselines in the repository. It verifies:
  - Dataset loading from JSONL
  - Clinical AI summarization
  - All evaluators (medication F1, format validator, entity extraction, etc.)
  - Metrics aggregation (including calibration ECE)
  - Quality gate pass/fail logic
  - Console report generation
  - Logging system
  - Setup and teardown phases

This is intended as both a test and a demonstration of the system behavior.
"""

import os
import sys
import json
import yaml

# Ensure src is on PYTHONPATH
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from medeval.logging_config import setup_logging, get_artifacts_dir, get_log_dir
from medeval.setup_teardown import SetupTeardownManager
from medeval.evaluation.runner import run
from medeval.reporting.console_report import print_report


def test_full_evaluation_pipeline():
    """Run the complete evaluation pipeline and verify all components work.
    
    This test:
      1. Sets up logging system and creates directories
      2. Runs setup phase (environment validation, cleanup)
      3. Loads clinical cases from the sample JSONL dataset
      4. Runs the ClinicalAI summarizer on each case
      5. Evaluates predictions with all evaluators
      6. Aggregates per-case metrics into dataset-level metrics
      7. Compares against the baseline thresholds (quality gate)
      8. Saves artifacts (predictions, metrics, quality gate results)
      9. Prints a human-readable console report
      10. Runs teardown phase (summary report, archiving)
    
    Expected outcome:
      - 'aggregated' key present with numeric metrics
      - 'passed' key indicates whether quality gate succeeded
      - 'failures' list contains human-readable failure reasons if any
      - 'per_case_results' list contains individual case evaluations
      - Logs and artifacts saved to .logs/ directory
    """
    # Construct absolute paths
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    config_path = os.path.join(root, 'medeval_config.yaml')
    dataset_path = os.path.join(root, 'datasets', 'clinical_cases.jsonl')
    baseline_path = os.path.join(root, 'baselines', 'production.json')
    
    # Load configuration
    config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as fh:
            config = yaml.safe_load(fh) or {}
    
    # Setup logging
    logger = setup_logging(config_path=config_path)
    logger.info("="*60)
    logger.info("FULL PIPELINE TEST STARTED")
    logger.info("="*60)
    logger.info(f"Configuration: {config_path}")
    logger.info(f"Dataset: {dataset_path}")
    logger.info(f"Baseline: {baseline_path}")
    
    # Get directories
    log_dir = get_log_dir()
    artifacts_dir = get_artifacts_dir()
    
    # Setup phase
    setup_manager = SetupTeardownManager(config)
    setup_success = setup_manager.setup(log_dir, artifacts_dir)
    
    if not setup_success:
        logger.error("Setup phase failed, aborting test")
        return None
    
    result = None
    try:
        # Run the evaluation pipeline
        logger.info("Running evaluation pipeline...")
        result = run(
            dataset_path,
            baseline_path,
            llm_client=None,
            save_artifacts=True,
            artifacts_dir=artifacts_dir
        )
        
        # Verify result structure
        assert 'aggregated' in result, "Result must contain 'aggregated' metrics"
        assert 'passed' in result, "Result must contain 'passed' boolean or None"
        assert 'failures' in result, "Result must contain 'failures' list"
        assert 'per_case_results' in result, "Result must contain 'per_case_results' list"
        
        aggregated = result['aggregated']
        passed = result['passed']
        failures = result['failures']
        
        # Verify aggregated metrics contain expected keys
        expected_metrics = [
            'med_precision', 'med_recall', 'med_f1',
            'format_score',
            'entity_med_precision', 'entity_med_recall', 'entity_med_f1',
            'entity_symptom_precision', 'entity_symptom_recall', 'entity_symptom_f1',
            'required_facts_score',
            'forbidden_score',
            'llm_judge_score',
            'calibration_ece'
        ]
        
        for metric in expected_metrics:
            assert metric in aggregated, f"Aggregated metrics missing '{metric}'"
        
        logger.info("="*60)
        logger.info("TEST RESULTS")
        logger.info("="*60)
        
        # Print the console report
        print_report(aggregated, passed, failures)
        print()
        
        # Save console report to artifacts
        if config.get('artifacts', {}).get('save_reports', True):
            report_file = artifacts_dir / "console_report.txt"
            with open(report_file, 'w', encoding='utf-8') as fh:
                fh.write("MedEval Report\n")
                fh.write("=" * 60 + "\n")
                for k, v in aggregated.items():
                    fh.write(f"{k}: {v}\n")
                fh.write("-" * 60 + "\n")
                fh.write(f"Quality gate: {'PASS' if passed else 'FAIL'}\n")
                if failures:
                    fh.write("Failures:\n")
                    for f in failures:
                        fh.write(f"  - {f}\n")
            logger.info(f"Console report saved to: {report_file}")
        
        # Print per-case summary
        logger.info("="*60)
        logger.info(f"Per-Case Results: {len(result['per_case_results'])} cases evaluated")
        logger.info("="*60)
        
        # Log a few sample cases
        for i, case_res in enumerate(result['per_case_results'][:2], 1):
            logger.info(f"Case {i} metrics:")
            for key, val in sorted(case_res.items()):
                if isinstance(val, (int, float)):
                    logger.debug(f"  {key}: {val:.3f}")
        
        if len(result['per_case_results']) > 2:
            logger.info(f"... and {len(result['per_case_results']) - 2} more case(s)")
        
        logger.info("="*60)
        if passed:
            logger.info("[PASS] Quality gate succeeded")
        elif passed is None:
            logger.info("[INFO] No baseline provided, metrics computed successfully")
        else:
            logger.error("[FAIL] Quality gate failed")
            for failure in failures:
                logger.error(f"  - {failure}")
        logger.info("="*60)
        
        return result
        
    finally:
        # Teardown phase
        setup_manager.teardown(log_dir, artifacts_dir, result)
        
        logger.info("="*60)
        logger.info("FULL PIPELINE TEST COMPLETED")
        logger.info("="*60)


def main():
    """Entry point when running this test file directly."""
    try:
        result = test_full_evaluation_pipeline()
        
        if result is None:
            print("\n[ERROR] Test setup failed")
            sys.exit(1)
        
        # Exit with appropriate code
        if result.get('passed') is False:
            sys.exit(1)
        sys.exit(0)
        
    except Exception as e:
        print(f"\n[ERROR] TEST FAILED WITH EXCEPTION: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
