"""Command-line interface for MedEval.

This module provides a CLI for running evaluations, viewing results, and managing
the MedEval system from the command line.

Usage:
    python -m medeval run --dataset <path> --baseline <path> [--mode <mode>]
    python -m medeval list-runs [--limit <n>]
    python -m medeval report --run <run_id>
    python -m medeval clean [--older-than <days>] [--keep <n>]
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
import yaml

from medeval.evaluation.runner import run
from medeval.logging_config import setup_logging, get_log_dir, get_artifacts_dir
from medeval.setup_teardown import SetupTeardownManager
from medeval.reporting.console_report import print_report


def cmd_run(args):
    """Run an evaluation with the specified dataset and baseline.
    
    Args:
        args: Parsed command-line arguments.
            - dataset: Path to dataset JSONL file
            - baseline: Path to baseline JSON file (optional)
            - mode: Execution mode (standard, fast, thorough, debug)
            - config: Path to config file (optional)
            - llm_client: LLM client to use (optional)
    
    Returns:
        Exit code (0 for success/pass, 1 for failure)
    """
    # Load configuration
    config_path = args.config or 'medeval_config.yaml'
    
    config = {}
    if Path(config_path).exists():
        with open(config_path, 'r', encoding='utf-8') as fh:
            config = yaml.safe_load(fh) or {}
    
    # Override mode if specified
    if args.mode:
        if 'execution' not in config:
            config['execution'] = {}
        config['execution']['mode'] = args.mode
    
    # Setup logging
    logger = setup_logging(config_path=config_path)
    logger.info("="*60)
    logger.info("MedEval CLI - Run Command")
    logger.info("="*60)
    logger.info(f"Dataset: {args.dataset}")
    logger.info(f"Baseline: {args.baseline or 'None'}")
    logger.info(f"Mode: {config.get('execution', {}).get('mode', 'standard')}")
    
    # Get directories
    log_dir = get_log_dir()
    artifacts_dir = get_artifacts_dir()
    
    # Setup phase
    setup_manager = SetupTeardownManager(config)
    setup_success = setup_manager.setup(log_dir, artifacts_dir)
    
    if not setup_success:
        logger.error("Setup phase failed")
        return 1
    
    result = None
    try:
        # Run evaluation
        result = run(
            dataset_path=args.dataset,
            baseline_path=args.baseline,
            llm_client=None,  # TODO: Support custom clients via CLI
            save_artifacts=True,
            artifacts_dir=artifacts_dir
        )
        
        # Print report
        print()
        print_report(
            result['aggregated'],
            result.get('passed'),
            result.get('failures', [])
        )
        print()
        
        # Log result summary
        logger.info("="*60)
        if result.get('passed'):
            logger.info("Result: PASSED")
        elif result.get('passed') is None:
            logger.info("Result: COMPLETED (no baseline)")
        else:
            logger.info("Result: FAILED")
            for failure in result.get('failures', []):
                logger.error(f"  - {failure}")
        logger.info("="*60)
        
        return 0 if result.get('passed', True) else 1
        
    finally:
        # Teardown phase
        if result:
            setup_manager.teardown(log_dir, artifacts_dir, result)


def cmd_list_runs(args):
    """List recent evaluation runs.
    
    Args:
        args: Parsed command-line arguments.
            - limit: Maximum number of runs to show
            - verbose: Show detailed information
    
    Returns:
        Exit code (always 0)
    """
    # Find .logs directory
    project_root = Path.cwd()
    log_base_dir = project_root / '.logs'
    
    if not log_base_dir.exists():
        print("No runs found (.logs directory does not exist)")
        return 0
    
    # Get all run directories
    run_dirs = [d for d in log_base_dir.iterdir() 
               if d.is_dir() and d.name.startswith('medeval_')]
    run_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    # Apply limit
    if args.limit:
        run_dirs = run_dirs[:args.limit]
    
    if not run_dirs:
        print("No runs found")
        return 0
    
    print(f"\nFound {len(run_dirs)} recent run(s):\n")
    print(f"{'Run ID':<25} {'Date':<20} {'Status':<12} {'Size (KB)':<10}")
    print("-" * 70)
    
    for run_dir in run_dirs:
        # Parse run ID
        run_id = run_dir.name.replace('medeval_', '')
        
        # Parse timestamp
        try:
            timestamp = datetime.strptime(run_id, "%Y%m%d_%H%M%S")
            date_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            date_str = "Unknown"
        
        # Get status from run_summary.json
        status = "Unknown"
        summary_file = run_dir / 'artifacts' / 'run_summary.json'
        if summary_file.exists():
            try:
                with open(summary_file, 'r', encoding='utf-8') as fh:
                    summary = json.load(fh)
                    if summary.get('result', {}).get('passed'):
                        status = "PASSED"
                    elif summary.get('result', {}).get('passed') is None:
                        status = "COMPLETED"
                    else:
                        status = "FAILED"
            except Exception:
                pass
        
        # Calculate size
        total_size = sum(f.stat().st_size for f in run_dir.rglob('*') if f.is_file())
        size_kb = total_size / 1024
        
        print(f"{run_id:<25} {date_str:<20} {status:<12} {size_kb:<10.1f}")
        
        # Verbose mode: show metrics
        if args.verbose and summary_file.exists():
            try:
                with open(summary_file, 'r', encoding='utf-8') as fh:
                    summary = json.load(fh)
                    metrics = summary.get('result', {}).get('key_metrics', {})
                    if metrics:
                        print(f"    Metrics: med_f1={metrics.get('med_f1', 'N/A'):.3f}, "
                              f"format_score={metrics.get('format_score', 'N/A'):.3f}, "
                              f"calibration_ece={metrics.get('calibration_ece', 'N/A'):.3f}")
            except Exception:
                pass
    
    print()
    return 0


def cmd_report(args):
    """Show detailed report for a specific run.
    
    Args:
        args: Parsed command-line arguments.
            - run: Run ID to show report for
            - format: Output format (console, json)
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Find run directory
    project_root = Path.cwd()
    log_base_dir = project_root / '.logs'
    run_dir = log_base_dir / f"medeval_{args.run}"
    
    if not run_dir.exists():
        print(f"Error: Run '{args.run}' not found")
        return 1
    
    # Load artifacts
    artifacts_dir = run_dir / 'artifacts'
    
    summary_file = artifacts_dir / 'run_summary.json'
    metrics_file = artifacts_dir / 'aggregated_metrics.json'
    quality_gate_file = artifacts_dir / 'quality_gate.json'
    
    if not summary_file.exists():
        print(f"Error: Run summary not found for '{args.run}'")
        return 1
    
    # Load data
    with open(summary_file, 'r', encoding='utf-8') as fh:
        summary = json.load(fh)
    
    metrics = {}
    if metrics_file.exists():
        with open(metrics_file, 'r', encoding='utf-8') as fh:
            metrics = json.load(fh)
    
    quality_gate = {}
    if quality_gate_file.exists():
        with open(quality_gate_file, 'r', encoding='utf-8') as fh:
            quality_gate = json.load(fh)
    
    # Output format
    if args.format == 'json':
        # JSON output
        output = {
            'run_id': args.run,
            'summary': summary,
            'metrics': metrics,
            'quality_gate': quality_gate
        }
        print(json.dumps(output, indent=2))
    else:
        # Console output
        print(f"\n{'='*60}")
        print(f"MedEval Run Report: {args.run}")
        print(f"{'='*60}\n")
        
        # Summary info
        print(f"Start Time:  {summary.get('start_time', 'N/A')}")
        print(f"End Time:    {summary.get('end_time', 'N/A')}")
        print(f"Duration:    {summary.get('duration_seconds', 0):.2f} seconds")
        print(f"Mode:        {summary.get('configuration', {}).get('mode', 'N/A')}")
        print(f"Cases:       {summary.get('result', {}).get('num_cases', 'N/A')}")
        
        # Quality gate
        passed = summary.get('result', {}).get('passed')
        if passed:
            print(f"Status:      PASSED ✓")
        elif passed is None:
            print(f"Status:      COMPLETED (no baseline)")
        else:
            print(f"Status:      FAILED ✗")
        
        print(f"\n{'-'*60}\n")
        
        # Metrics
        print("Aggregated Metrics:\n")
        key_metrics = summary.get('result', {}).get('key_metrics', {})
        for key, value in sorted(key_metrics.items()):
            if isinstance(value, (int, float)):
                print(f"  {key:<30} {value:.4f}")
            elif isinstance(value, list):
                print(f"  {key:<30} {value}")
        
        # Failures
        failures = summary.get('result', {}).get('failures', [])
        if failures:
            print(f"\n{'-'*60}\n")
            print("Quality Gate Failures:\n")
            for failure in failures:
                print(f"  - {failure}")
        
        print(f"\n{'='*60}\n")
    
    return 0


def cmd_clean(args):
    """Clean old evaluation runs.
    
    Args:
        args: Parsed command-line arguments.
            - older_than: Delete runs older than N days
            - keep: Keep N most recent runs
            - dry_run: Show what would be deleted without deleting
    
    Returns:
        Exit code (0 for success)
    """
    # Find .logs directory
    project_root = Path.cwd()
    log_base_dir = project_root / '.logs'
    
    if not log_base_dir.exists():
        print("No runs found (.logs directory does not exist)")
        return 0
    
    # Get all run directories
    run_dirs = [d for d in log_base_dir.iterdir() 
               if d.is_dir() and d.name.startswith('medeval_')]
    run_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    # Determine which to delete
    to_delete = []
    
    if args.older_than:
        # Delete runs older than N days
        cutoff_time = datetime.now() - timedelta(days=args.older_than)
        for run_dir in run_dirs:
            mod_time = datetime.fromtimestamp(run_dir.stat().st_mtime)
            if mod_time < cutoff_time:
                to_delete.append(run_dir)
    elif args.keep is not None:
        # Keep N most recent runs, delete the rest
        to_delete = run_dirs[args.keep:]
    else:
        print("Error: Must specify --older-than or --keep")
        return 1
    
    if not to_delete:
        print("No runs to delete")
        return 0
    
    # Show what will be deleted
    print(f"\nWill delete {len(to_delete)} run(s):\n")
    for run_dir in to_delete:
        run_id = run_dir.name.replace('medeval_', '')
        size = sum(f.stat().st_size for f in run_dir.rglob('*') if f.is_file())
        size_kb = size / 1024
        print(f"  {run_id} ({size_kb:.1f} KB)")
    
    if args.dry_run:
        print("\n(Dry run - nothing deleted)")
        return 0
    
    # Confirm
    confirm = input("\nProceed with deletion? [y/N]: ")
    if confirm.lower() != 'y':
        print("Cancelled")
        return 0
    
    # Delete runs
    import shutil
    deleted_count = 0
    for run_dir in to_delete:
        try:
            shutil.rmtree(run_dir)
            deleted_count += 1
        except Exception as e:
            print(f"Error deleting {run_dir.name}: {e}")
    
    print(f"\nDeleted {deleted_count} run(s)")
    return 0


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='MedEval - Clinical AI Evaluation Framework',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run an evaluation')
    run_parser.add_argument('--dataset', required=True, help='Path to dataset JSONL file')
    run_parser.add_argument('--baseline', help='Path to baseline JSON file')
    run_parser.add_argument('--mode', choices=['standard', 'fast', 'thorough', 'debug'],
                           help='Execution mode')
    run_parser.add_argument('--config', help='Path to config file (default: medeval_config.yaml)')
    run_parser.set_defaults(func=cmd_run)
    
    # List runs command
    list_parser = subparsers.add_parser('list-runs', help='List recent evaluation runs')
    list_parser.add_argument('--limit', type=int, default=10, help='Maximum runs to show')
    list_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed information')
    list_parser.set_defaults(func=cmd_list_runs)
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Show detailed report for a run')
    report_parser.add_argument('--run', required=True, help='Run ID (e.g., 20260828_160129)')
    report_parser.add_argument('--format', choices=['console', 'json'], default='console',
                              help='Output format')
    report_parser.set_defaults(func=cmd_report)
    
    # Clean command
    clean_parser = subparsers.add_parser('clean', help='Clean old evaluation runs')
    clean_group = clean_parser.add_mutually_exclusive_group(required=True)
    clean_group.add_argument('--older-than', type=int, metavar='DAYS',
                            help='Delete runs older than N days')
    clean_group.add_argument('--keep', type=int, metavar='N',
                            help='Keep N most recent runs')
    clean_parser.add_argument('--dry-run', action='store_true',
                             help='Show what would be deleted without deleting')
    clean_parser.set_defaults(func=cmd_clean)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
