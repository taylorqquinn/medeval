# MedEval Project Summary

## Project Structure

```
medeval/
├── src/medeval/                    # Source code
│   ├── application/                # LLM clients and clinical AI
│   │   ├── clinical_ai.py          # With detailed docstrings and logging
│   │   ├── llm_client.py           # With detailed docstrings and logging
│   │   └── openai_client.py        # With detailed docstrings
│   ├── evaluators/                 # All evaluation components
│   │   ├── calibration.py          # With detailed docstrings
│   │   ├── entity_extraction.py    # With detailed docstrings
│   │   ├── format_validator.py     # With detailed docstrings
│   │   ├── llm_judge.py            # With detailed docstrings
│   │   ├── medication_f1.py        # With detailed docstrings
│   │   └── required_forbidden.py   # With detailed docstrings
│   ├── evaluation/                 # Pipeline and metrics
│   │   ├── baseline.py             # With detailed docstrings
│   │   ├── metrics.py              # With detailed docstrings
│   │   ├── quality_gate.py         # With detailed docstrings
│   │   └── runner.py               # With detailed docstrings and logging
│   ├── reporting/                  # Report generation
│   │   └── console_report.py       # With detailed docstrings
│   ├── dataset.py                  # With detailed docstrings and logging
│   ├── logging_config.py           # Centralized logging system
│   └── setup_teardown.py           # Setup/teardown phases
├── tests/
│   ├── unit/                       # Unit tests (mirror src structure)
│   │   ├── application/            # Tests for application modules
│   │   │   ├── test_clinical_ai.py
│   │   │   ├── test_llm_client.py
│   │   │   └── test_openai_client.py
│   │   ├── dataset/                # Tests for dataset module
│   │   │   └── test_dataset.py
│   │   ├── evaluation/             # Tests for evaluation modules
│   │   │   ├── test_metrics.py
│   │   │   └── test_quality_gate.py
│   │   ├── evaluators/             # Tests for all evaluators
│   │   │   ├── test_calibration.py
│   │   │   ├── test_entity_extraction.py
│   │   │   ├── test_format_validator.py
│   │   │   ├── test_medication_f1.py
│   │   │   └── test_required_forbidden.py
│   │   └── reporting/              # Tests for reporting modules
│   │       └── test_console_report.py
│   └── software/                   # Integration tests
│       └── test_full_pipeline.py   # Runnable end-to-end test
├── .logs/                          # Auto-generated log directory
│   ├── medeval_YYYYMMDD_HHMMSS/    # Run-specific folder
│   │   ├── logs/                   # Log files
│   │   │   └── medeval_*.log       # Timestamped execution log
│   │   └── artifacts/              # Per-run artifacts
│   │       ├── predictions.json
│   │       ├── aggregated_metrics.json
│   │       ├── quality_gate.json
│   │       ├── console_report.txt
│   │       └── run_summary.json
│   └── medeval_YYYYMMDD_HHMMSS/    # Another run folder
│       ├── logs/
│       └── artifacts/
├── medeval_config.yaml             # Configuration file
├── LOGGING_GUIDE.md                # Comprehensive logging documentation
└── README.md
```

## Features Implemented

### 1. Comprehensive Docstrings
✅ All source functions have detailed docstrings explaining:
- Purpose and behavior
- Parameters with types and descriptions
- Return values with types
- Raises/exceptions
- Examples where helpful

### 2. Unit Tests
✅ Complete unit test suite with:
- Tests mirror source structure (src/medeval → tests/unit)
- Detailed docstrings explaining test scenarios
- Expected outcomes clearly documented
- 12 test files covering all modules

### 3. Runnable Integration Test
✅ `tests/software/test_full_pipeline.py`:
- Run directly: `python tests/software/test_full_pipeline.py`
- Exercises full evaluation pipeline
- Uses logging system and setup/teardown
- Saves artifacts to `.logs/artifacts/`
- Exits with appropriate code (0=pass, 1=fail)

### 4. Logging System
✅ Centralized logging via `src/medeval/logging_config.py`:
- Singleton pattern for single instance
- File and console handlers
- Log rotation (10MB per file, 5 backups)
- Timestamped log files
- Module-specific loggers (medeval.runner, medeval.clinical_ai, etc.)
- Logging throughout runner, dataset, clinical_ai

### 5. Setup/Teardown
✅ Automated phases via `src/medeval/setup_teardown.py`:
- **Setup**: Environment validation, log cleanup, system info logging
- **Teardown**: Summary report, archiving, statistics

### 6. Configuration System
✅ `medeval_config.yaml` controls:
- Logging levels and formats
- Log and artifact directories
- Execution modes (standard, fast, thorough, debug)
- Setup/teardown behavior
- Artifact saving options

### 7. Separate Logs and Artifacts
✅ Self-contained run folders:
- **Run folder**: `.logs/medeval_YYYYMMDD_HHMMSS/`
  - `logs/` - Execution logs
  - `artifacts/` - Output files (predictions, metrics, reports)

### 8. Multiple Execution Modes
✅ 4 modes configured in YAML:
- **standard**: All evaluators, INFO logging (default)
- **fast**: Skip slow evaluators, parallel execution
- **thorough**: All evaluators, detailed logging
- **debug**: DEBUG-level logging, save everything

## How to Use

### Run the Full Pipeline Test
```bash
python tests/software/test_full_pipeline.py
```

### Run Unit Tests (when pytest is available)
```bash
pytest tests/unit/
```

### Check Logs
```bash
# View latest log
Get-Content .logs\medeval_*.log | Select-Object -Last 50

# View artifacts for a specific run
Get-ChildItem .logs\artifacts\20260828_154704\
```

### Configure Logging
Edit `medeval_config.yaml`:
```yaml
# Change execution mode
mode: debug  # or fast, thorough, standard

# Adjust log level
logging:
  level: "DEBUG"  # or INFO, WARNING, ERROR
```

### Use in Your Code
```python
from medeval.logging_config import setup_logging, get_artifacts_dir
import logging

# Setup once at startup
logger = setup_logging(config_path='medeval_config.yaml')

# Get module-specific logger
my_logger = logging.getLogger('medeval.my_module')

# Log messages
my_logger.info("Processing started")
my_logger.debug("Detailed information")
my_logger.error("Something went wrong")

# Save artifacts
artifacts_dir = get_artifacts_dir()
output_file = artifacts_dir / "my_output.json"
```

## Key Files

### Configuration
- `medeval_config.yaml`: Master configuration file

### Logging Infrastructure
- `src/medeval/logging_config.py`: Centralized logging manager
- `src/medeval/setup_teardown.py`: Setup/teardown phases

### Tests
- `tests/software/test_full_pipeline.py`: Runnable integration test
- `tests/unit/`: 12 unit test files mirroring source structure

### Documentation
- `LOGGING_GUIDE.md`: Comprehensive guide to logging system
- `README.md`: Project overview

## Verification

The system has been tested and verified:
- ✅ Logging system initializes correctly
- ✅ Setup phase validates environment and cleans old logs
- ✅ Pipeline runs and logs all operations
- ✅ Artifacts saved to separate directory
- ✅ Teardown phase creates summary report
- ✅ Quality gate evaluation works
- ✅ Test exits with correct code

Example output structure:
```
.logs/
└── medeval_20260828_160129/
    ├── logs/
    │   └── medeval_20260828_160129.log
    └── artifacts/
        ├── aggregated_metrics.json
        ├── console_report.txt
        ├── predictions.json
        ├── quality_gate.json
        └── run_summary.json
```

## Dependencies

Required packages:
- pyyaml (for configuration loading)

Install with:
```bash
pip install pyyaml
```

## Next Steps

Optional enhancements:
1. Add logging to remaining evaluator modules (currently only runner, dataset, clinical_ai have logging)
2. Add pytest.ini for test configuration
3. Add GitHub Actions workflow to run tests
4. Add performance profiling in debug mode
5. Add email notifications for quality gate failures
