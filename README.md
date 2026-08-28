# MedEval

A comprehensive evaluation framework for testing clinical AI systems. MedEval provides standardized metrics, quality gates, and detailed logging to validate AI-generated medical summaries against ground truth.

## Features

✅ **Comprehensive Evaluators**: 7 built-in evaluators for medical AI assessment
- Medication F1 Score (precision/recall)
- Format Validation
- Entity Extraction (medications, symptoms)
- Required Facts Checking
- Forbidden Content Detection
- LLM Judge (semantic quality)
- Calibration Analysis (Expected Calibration Error)

✅ **Quality Gates**: Baseline comparison with pass/fail thresholds

✅ **Detailed Logging**: Complete execution traces with artifacts

✅ **Multiple Execution Modes**: Standard, Fast, Thorough, Debug

✅ **Self-Contained Runs**: Each run creates a timestamped folder with all logs and artifacts

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/taylorqquinn/medeval.git
cd medeval

# Install dependencies
pip install -r requirements.txt
```

### Running Tests

```bash
# Run the full integration test
python tests\software\test_full_pipeline.py

# Or run with CLI (coming soon)
python -m medeval run --dataset datasets/clinical_cases.jsonl
```

### Running Unit Tests

```bash
# Run all unit tests (requires pytest)
pytest tests/unit/

# Run specific test module
pytest tests/unit/evaluators/test_medication_f1.py
```

## Project Structure

```
medeval/
├── src/medeval/              # Source code
│   ├── application/          # LLM clients and clinical AI
│   ├── evaluators/           # Evaluation components
│   ├── evaluation/           # Pipeline and metrics
│   ├── reporting/            # Report generation
│   ├── logging_config.py     # Logging system
│   └── setup_teardown.py     # Setup/teardown phases
├── tests/
│   ├── unit/                 # Unit tests (mirror src structure)
│   └── software/             # Integration tests
├── datasets/                 # Test datasets
├── baselines/                # Quality gate baselines
├── medeval_config.yaml       # Configuration
└── .logs/                    # Generated logs and artifacts
```

## Configuration

All system behavior is controlled by `medeval_config.yaml`:

```yaml
# Execution mode: standard, fast, thorough, debug
execution:
  mode: "standard"

# Logging configuration
logging:
  console_level: "INFO"
  file_level: "DEBUG"

# Setup/teardown
setup:
  max_log_runs: 10  # Keep 10 most recent runs
```

See [LOGGING_GUIDE.md](LOGGING_GUIDE.md) for complete configuration documentation.

## Output Structure

Each run creates a self-contained folder:

```
.logs/
└── medeval_20260828_160129/
    ├── logs/
    │   └── medeval_20260828_160129.log
    └── artifacts/
        ├── predictions.json
        ├── aggregated_metrics.json
        ├── quality_gate.json
        ├── console_report.txt
        └── run_summary.json
```

## Example Usage

### From Python

```python
from medeval.evaluation.runner import run

# Run evaluation
result = run(
    dataset_path='datasets/clinical_cases.jsonl',
    baseline_path='baselines/production.json'
)

# Check results
if result['passed']:
    print("Quality gate PASSED")
else:
    print("Quality gate FAILED:", result['failures'])
```

### Viewing Results

```powershell
# List all runs
Get-ChildItem .logs

# View latest log
Get-Content .logs\medeval_*\logs\*.log | Select-Object -Last 50

# View metrics for a run
Get-Content .logs\medeval_20260828_160129\artifacts\aggregated_metrics.json
```

## Documentation

- [LOGGING_GUIDE.md](LOGGING_GUIDE.md) - Complete logging system documentation
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Project overview and implementation details

## Development

### Adding Custom Evaluators

Create a new evaluator in `src/medeval/evaluators/`:

```python
class MyCustomEvaluator:
    """Your custom evaluation logic."""
    
    def evaluate(self, prediction: str, case: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single case.
        
        Args:
            prediction: AI-generated summary
            case: Ground truth case data
            
        Returns:
            Dictionary of metrics
        """
        # Your evaluation logic here
        return {"my_metric": score}
```

Then register it in `src/medeval/evaluation/runner.py`.

### Running in Different Modes

Edit `medeval_config.yaml`:

```yaml
execution:
  mode: "debug"  # Options: standard, fast, thorough, debug
```

- **standard**: All evaluators, INFO logging (production)
- **fast**: Skip slow evaluators, parallel execution (quick checks)
- **thorough**: Detailed logging, save intermediates (investigation)
- **debug**: DEBUG-level logs, save everything (troubleshooting)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## License

[Add your license here]

## Contact

For questions or issues, please open a GitHub issue or contact the maintainers.
