# MedEval Logging System Guide

## Overview

MedEval includes a comprehensive logging system that tracks all evaluation operations, captures detailed execution information, and separates logs from artifacts for better organization.

## Quick Start

Run the full pipeline test to see logging in action:

```bash
python tests/software/test_full_pipeline.py
```

This will:
1. Initialize the logging system
2. Run setup phase (environment validation, log cleanup)
3. Execute the full evaluation pipeline
4. Run teardown phase (summary generation, archiving)
5. Create logs and artifacts in `.logs/`

## Directory Structure

Each test run creates a self-contained timestamped folder:

```
.logs/
└── medeval_YYYYMMDD_HHMMSS/       # Run-specific folder
    ├── logs/                       # Log files
    │   └── medeval_YYYYMMDD_HHMMSS.log
    └── artifacts/                  # Output artifacts
        ├── predictions.json
        ├── aggregated_metrics.json
        ├── quality_gate.json
        ├── console_report.txt
        └── run_summary.json
```

### Example

```
.logs/
├── medeval_20260828_160129/
│   ├── logs/
│   │   └── medeval_20260828_160129.log
│   └── artifacts/
│       ├── predictions.json
│       ├── aggregated_metrics.json
│       ├── quality_gate.json
│       ├── console_report.txt
│       └── run_summary.json
└── medeval_20260828_160144/
    ├── logs/
    │   └── medeval_20260828_160144.log
    └── artifacts/
        ├── predictions.json
        ├── aggregated_metrics.json
        ├── quality_gate.json
        ├── console_report.txt
        └── run_summary.json
```

### Benefits

- **Self-contained**: Each run has all its logs and artifacts in one folder
- **Easy to manage**: Delete a run by removing its folder
- **Easy to share**: Zip and share a complete run folder
- **Automatic cleanup**: Old runs are automatically deleted based on `max_log_runs`

### Logs vs Artifacts

- **Logs** (`logs/` subfolder): Timestamped execution traces with INFO/DEBUG/WARNING/ERROR messages
- **Artifacts** (`artifacts/` subfolder): Structured output files from evaluation runs

## Configuration

All logging behavior is controlled by `medeval_config.yaml`:

```yaml
logging:
  level: "INFO"                        # Default log level
  log_dir: ".logs"                     # Where to store logs
  format: "[%(asctime)s] %(name)s - %(levelname)s - %(message)s"
  date_format: "%Y-%m-%d %H:%M:%S"
  
  file:
    enabled: true                      # Write logs to file
    max_bytes: 10485760               # 10 MB per log file
    backup_count: 5                   # Keep 5 rotated log files
    
  console:
    enabled: true                      # Print logs to console
    level: "INFO"                      # Console log level

artifacts:
  enabled: true                        # Save artifacts
  artifacts_dir: ".logs/artifacts"   # Where to store artifacts
  save_predictions: true              # Save predictions.json
  save_metrics: true                  # Save aggregated_metrics.json
  save_quality_gate: true             # Save quality_gate.json
  save_reports: true                  # Save console_report.txt
```

## Execution Modes

MedEval supports 4 execution modes with different logging and evaluation behaviors:

### 1. Standard Mode (Default)

```yaml
mode: standard
modes:
  standard:
    enable_all_evaluators: true
    parallel_execution: false
    detailed_logging: false
```

- All evaluators enabled
- Sequential execution
- INFO-level logging
- Good for production runs

### 2. Fast Mode

```yaml
mode: fast
modes:
  fast:
    enable_all_evaluators: false
    skip_evaluators: ["LLMJudge", "Calibration"]
    parallel_execution: true
    detailed_logging: false
```

- Skips slow evaluators
- Parallel execution
- Minimal logging
- Good for quick checks

### 3. Thorough Mode

```yaml
mode: thorough
modes:
  thorough:
    enable_all_evaluators: true
    parallel_execution: false
    detailed_logging: true
    save_intermediate_results: true
```

- All evaluators
- Detailed INFO logging
- Saves intermediate results
- Good for investigation

### 4. Debug Mode

```yaml
mode: debug
modes:
  debug:
    enable_all_evaluators: true
    parallel_execution: false
    detailed_logging: true
    save_intermediate_results: true
    log_level_override: "DEBUG"
```

- All evaluators
- DEBUG-level logging
- Saves everything
- Good for troubleshooting

## Setup and Teardown

### Setup Phase

Runs automatically before evaluation:
- Validates environment (Python version, required packages)
- Cleans old logs (keeps N most recent runs)
- Logs system information (platform, Python version, working directory)
- Creates necessary directories

Configuration:

```yaml
setup:
  enabled: true
  validate_environment: true
  clean_old_logs: true
  max_log_runs: 10          # Keep 10 most recent runs
```

### Teardown Phase

Runs automatically after evaluation:
- Creates summary report with run metadata
- Archives artifacts for the run
- Logs execution statistics (duration, cases evaluated, quality gate result)

Configuration:

```yaml
teardown:
  enabled: true
  create_summary: true
  archive_artifacts: false   # Optional: compress artifacts
```

## Using the Logging System

### In Your Code

```python
from medeval.logging_config import setup_logging, get_artifacts_dir, get_log_dir
import logging

# Initialize logging (do this once at startup)
logger = setup_logging(config_path='medeval_config.yaml')

# Get a module-specific logger
module_logger = logging.getLogger('medeval.my_module')

# Log at different levels
module_logger.debug("Detailed diagnostic information")
module_logger.info("General information about execution")
module_logger.warning("Warning about potential issues")
module_logger.error("Error that occurred during execution")

# Get artifact directory for saving files
artifacts_dir = get_artifacts_dir()
output_file = artifacts_dir / "my_output.json"
```

### In Evaluation Runner

```python
from medeval.logging_config import setup_logging, get_artifacts_dir
from medeval.setup_teardown import SetupTeardownManager
from medeval.evaluation.runner import run

# Setup
config = yaml.safe_load(open('medeval_config.yaml'))
logger = setup_logging(config_path='medeval_config.yaml')
setup_manager = SetupTeardownManager(config)

log_dir = get_log_dir()
artifacts_dir = get_artifacts_dir()
setup_manager.setup(log_dir, artifacts_dir)

try:
    # Run evaluation
    result = run(
        dataset_path='datasets/clinical_cases.jsonl',
        baseline_path='baselines/production.json',
        save_artifacts=True,
        artifacts_dir=artifacts_dir
    )
finally:
    # Teardown
    setup_manager.teardown(log_dir, artifacts_dir, result)
```

## Log Messages

The system logs at different levels throughout execution:

### INFO Level
- Pipeline start/completion
- Dataset loading
- Case processing progress
- Metric aggregation
- Quality gate results
- Setup/teardown phases

### DEBUG Level
- Individual evaluator outputs
- Intermediate calculations
- Environment validation details
- File operations

### WARNING Level
- Missing optional dependencies
- Deprecated features
- Performance concerns

### ERROR Level
- Failed evaluations
- File I/O errors
- Configuration errors

## Artifacts

Each run creates several artifact files:

### predictions.json
```json
[
  {
    "case_id": "case-001",
    "input": {...},
    "prediction": "Patient summary...",
    "metrics": {...}
  }
]
```

### aggregated_metrics.json
```json
{
  "med_f1": 0.95,
  "format_score": 1.0,
  "entity_med_f1": 0.92,
  "calibration_ece": 0.08,
  ...
}
```

### quality_gate.json
```json
{
  "passed": true,
  "failures": [],
  "thresholds": {...},
  "actual": {...}
}
```

### run_summary.json
```json
{
  "run_id": "20260828_154704",
  "start_time": "2026-08-28T15:47:04",
  "end_time": "2026-08-28T15:47:04",
  "duration_seconds": 0.06,
  "configuration": {...},
  "result": {...}
}
```

### console_report.txt
Human-readable text report with all metrics and quality gate status.

## Troubleshooting

### Logs not appearing
- Check `logging.enabled` and `logging.console.enabled` in config
- Verify log level is appropriate (DEBUG shows most, ERROR shows least)

### Artifacts not being saved
- Check `artifacts.enabled` in config
- Verify `save_artifacts=True` is passed to runner
- Check write permissions on `.logs/` directory

### Old logs accumulating
- Adjust `setup.max_log_runs` to keep fewer runs
- Enable `teardown.archive_artifacts` to compress old runs
- Manually delete old runs from `.logs/artifacts/`

### Performance issues with logging
- Switch to "fast" mode
- Disable `detailed_logging` in mode configuration
- Set `logging.file.enabled: false` to skip file writes
- Increase `logging.level` to WARNING or ERROR

## Best Practices

1. **Always use setup/teardown** - Ensures clean environment and complete artifact collection
2. **Choose appropriate mode** - Use "fast" for CI, "debug" for investigation
3. **Monitor log file sizes** - Adjust `max_bytes` and `backup_count` if logs grow too large
4. **Clean old artifacts regularly** - Set reasonable `max_log_runs` value
5. **Use module-specific loggers** - `logging.getLogger('medeval.module_name')`
6. **Log at appropriate levels** - DEBUG for details, INFO for progress, ERROR for failures
7. **Save important artifacts** - Enable relevant `save_*` options in config

## Example Workflows

### Development Testing
```yaml
mode: debug
logging:
  level: "DEBUG"
  console:
    enabled: true
setup:
  clean_old_logs: false  # Keep all logs for investigation
```

### CI/CD Pipeline
```yaml
mode: fast
logging:
  level: "WARNING"
  console:
    enabled: true
  file:
    enabled: false  # No need for log files in CI
artifacts:
  save_reports: true
  save_predictions: false  # Save space
```

### Production Evaluation
```yaml
mode: standard
logging:
  level: "INFO"
artifacts:
  enabled: true
  save_predictions: true
  save_metrics: true
  save_quality_gate: true
setup:
  max_log_runs: 50  # Keep more runs in production
teardown:
  archive_artifacts: true  # Compress old runs
```

## Managing Log Files

### Viewing Logs

Each run is self-contained in its own folder:

```powershell
# List all runs
Get-ChildItem .logs

# View latest log file
Get-Content .logs\medeval_*\logs\*.log | Select-Object -Last 50

# View specific run's log
Get-Content .logs\medeval_20260828_160129\logs\medeval_20260828_160129.log

# View artifacts for a run
Get-ChildItem .logs\medeval_20260828_160129\artifacts

# View specific artifact
Get-Content .logs\medeval_20260828_160129\artifacts\run_summary.json
```

### Cleaning Up Logs

```powershell
# Delete a specific run
Remove-Item .logs\medeval_20260828_160129 -Recurse

# Delete all runs older than 30 days
Get-ChildItem .logs -Directory | Where-Object {$_.CreationTime -lt (Get-Date).AddDays(-30)} | Remove-Item -Recurse

# Zip and archive a run
Compress-Archive -Path .logs\medeval_20260828_160129 -DestinationPath archives\run_20260828_160129.zip
```

### Sharing Results

Since each run is self-contained, you can easily share complete results:

```powershell
# Zip a run for sharing
Compress-Archive -Path .logs\medeval_20260828_160129 -DestinationPath medeval_results.zip

# Extract received run
Expand-Archive -Path medeval_results.zip -DestinationPath .logs\
```

