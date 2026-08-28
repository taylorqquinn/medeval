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

✅ **Real OpenAI Integration**: Production-ready API integration
- GPT-4, GPT-3.5-turbo, and other models
- Automatic cost tracking with budget enforcement
- Rate limiting to prevent quota exhaustion
- Supports multiple models for comparison

✅ **Quality Gates**: Baseline comparison with pass/fail thresholds

✅ **Detailed Logging**: Complete execution traces with artifacts

✅ **Multiple Execution Modes**: Standard, Fast, Thorough, Debug

✅ **CLI Interface**: Professional command-line tool
- Run evaluations
- View reports
- Compare runs
- Manage old logs

✅ **Self-Contained Runs**: Each run creates a timestamped folder with all logs and artifacts

## Quick Start

### Installation

**Option A: Using Poetry (Recommended)**

```bash
# Clone the repository
git clone https://github.com/taylorqquinn/medeval.git
cd medeval

# Install Poetry (if not already installed)
# Windows PowerShell:
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Install dependencies (includes OpenAI)
.\poetry.ps1 install --extras openai

# Or without the helper script:
poetry install --extras openai
```

**Option B: Using pip**

```bash
# Clone the repository
git clone https://github.com/taylorqquinn/medeval.git
cd medeval

# Install dependencies
pip install -r requirements.txt

# Optional: For real OpenAI integration
pip install openai>=1.0.0
```

### Basic Usage

**With Poetry:**
```bash
# Run evaluation
.\poetry.ps1 run medeval run --dataset datasets/clinical_cases.jsonl

# List recent runs
.\poetry.ps1 run medeval list-runs

# View detailed report
.\poetry.ps1 run medeval report --run <run_id>

# Run tests
.\poetry.ps1 run python tests\software\test_full_pipeline.py
```

**Without Poetry (Test Mode - No API calls):**
```bash
# Set Python path
$env:PYTHONPATH="$pwd\src"  # Windows
export PYTHONPATH="$PWD/src"  # Linux/Mac

# Run evaluation
python -m medeval run --dataset datasets/clinical_cases.jsonl
```

**Production Mode (Real OpenAI API):**
```bash
# Set API key
$env:OPENAI_API_KEY="sk-your-key-here"

# Enable OpenAI in config
# Edit medeval_config.yaml: llm.client_type: "openai"

# Run evaluation with Poetry
.\poetry.ps1 run medeval run --dataset datasets/clinical_cases.jsonl --mode standard

# Or without Poetry
python -m medeval run --dataset datasets/clinical_cases.jsonl --mode standard

# View cost report
python -m medeval report --run <run_id>
```

See [OPENAI_INTEGRATION_GUIDE.md](OPENAI_INTEGRATION_GUIDE.md) for detailed configuration options.

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
