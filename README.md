# MedEval Framework

**Framework-only evaluation core for testing clinical AI systems.**

MedEval is the library layer: data models, evaluators, evaluation runners, and analysis utilities. It does **not** ship a CLI, application runtime, or OpenAI client in this repository.

If you want a concept-first deep dive, read **`AI_TESTING_HANDBOOK.html`**. This README is the concise API and architecture reference.

## What this repository contains

- **Core models** for test cases and predictions (`ClinicalCase`, `Prediction`, `RetrievedDocument`)
- **Deterministic, judge-based, retrieval, safety, performance, and calibration evaluators**
- **A framework-level runner** for per-case and aggregate evaluation
- **Utility modules** for baselines, quality gates, statistics, metric aggregation, and human review workflows
- **A plugin hook** for third-party evaluators via the `medeval.evaluators` entry-point group

## Framework-only architecture

This repository intentionally stops at the evaluation framework boundary:

1. **`medeval` (this repo)** – evaluation engine and reusable library code
2. **[medevalHelpers](https://github.com/taylorqquinn/medevalHelpers)** – sibling repo for CLI/helpers/runtime glue
3. **[medevalTests](https://github.com/taylorqquinn/medevalTests)** – sibling repo for shareable datasets and test suites

That split matches the package metadata in `pyproject.toml`: **"framework only (no CLI)"**.

## Installation

```bash
pip install medeval-framework
```

From source:

```bash
git clone https://github.com/taylorqquinn/medeval.git
cd medeval
pip install -e .
```

## Top-level imports

The package root exports the framework entry points most users need:

```python
from medeval import ClinicalCase, Prediction, EvaluationRunner, load_dataset
```

For `RetrievedDocument`, import from `medeval.models`:

```python
from medeval.models import RetrievedDocument
```

## Quick start

```python
from medeval import ClinicalCase, Prediction, EvaluationRunner
from medeval.evaluators import MedicationF1Evaluator, RequiredFactsEvaluator

case = ClinicalCase(
    id="case_001",
    text="Patient with chest pain and shortness of breath.",
    symptoms=["chest pain", "shortness of breath"],
    medications=["aspirin", "nitroglycerin"],
    required_facts=["cardiac", "emergency"],
    forbidden_facts=["definitely cancer"],
    gold_summary={"summary_text": "Likely acute coronary syndrome requiring urgent workup."},
)

prediction = Prediction(
    case_id="case_001",
    summary_text="Cardiac emergency is possible. Medications: aspirin, metoprolol.",
    medications=["aspirin", "metoprolol"],
    confidence=0.82,
)

runner = EvaluationRunner(
    evaluators=[
        MedicationF1Evaluator(),
        RequiredFactsEvaluator(),
    ]
)

case_result = runner.evaluate_case(case, prediction)
print(case_result.metrics)
# {'med_precision': 0.5, 'med_recall': 0.5, 'med_f1': 0.5,
#  'required_facts_score': 1.0, 'required_missing': []}

results = runner.run([case], [prediction])
print(results.aggregated_metrics)
# {'med_precision_mean': 0.5, 'med_precision_min': 0.5, 'med_precision_max': 0.5, ...}
print(results.quality_gate_passed)
# None unless baseline_path was supplied to the runner
```

### Runner API surface

- `EvaluationRunner.evaluate_case(case, prediction) -> CaseResult`
  - `CaseResult.case_id`
  - `CaseResult.metrics`
  - `CaseResult.errors`
- `EvaluationRunner.run(cases, predictions) -> EvaluationResults`
  - `EvaluationResults.case_results`
  - `EvaluationResults.aggregated_metrics`
  - `EvaluationResults.quality_gate_passed`

`EvaluationRunner.run()` aggregates numeric metrics into `{metric}_mean`, `{metric}_min`, and `{metric}_max` keys.

## Data model reference

### `ClinicalCase` (`src/medeval/models.py`)

```python
ClinicalCase(
    id: str,
    text: str,
    symptoms: list[str],
    medications: list[str],
    required_facts: list[str],
    forbidden_facts: list[str],
    gold_summary: dict[str, object],
    relevant_doc_ids: list[str] | None = None,
    source_text: str | None = None,
    is_adversarial: bool = False,
    adversarial_type: str | None = None,
)
```

### `Prediction` (`src/medeval/models.py`)

```python
Prediction(
    case_id: str,
    summary_text: str,
    medications: list[str],
    confidence: float | None = None,
    retrieved_docs: list[RetrievedDocument] | None = None,
    latency_ms: float | None = None,
    cost_usd: float | None = None,
    tokens_used: int | None = None,
    safety_flags: list[str] | None = None,
    detected_attacks: list[str] | None = None,
)
```

### `RetrievedDocument` (`src/medeval/models.py`)

```python
RetrievedDocument(
    doc_id: str,
    text: str,
    score: float,
    rank: int,
    metadata: dict[str, object] = {},
)
```

## Dataset loading

`src/medeval/dataset.py` exposes:

```python
from medeval.dataset import load_cases, load_dataset
```

`load_cases(path)` reads JSONL into `ClinicalCase` objects, but today it only populates these fields from each line:

- `id`
- `text`
- `symptoms`
- `medications`
- `required_facts`
- `forbidden_facts`
- `gold_summary`

If you need `relevant_doc_ids`, `source_text`, `is_adversarial`, or `adversarial_type`, instantiate `ClinicalCase` directly (or use your own loader) so those fields are preserved.

## Evaluator catalog

All built-in evaluator classes are exported from `medeval.evaluators`.

| Module | Class | Primary output keys |
| --- | --- | --- |
| `evaluators/medication_f1.py` | `MedicationF1Evaluator` | `med_precision`, `med_recall`, `med_f1` |
| `evaluators/required_facts.py` | `RequiredFactsEvaluator` | `required_facts_score`, `required_missing` |
| `evaluators/forbidden_facts.py` | `ForbiddenFactsEvaluator` | `forbidden_score`, `forbidden_found` |
| `evaluators/entity_extraction.py` | `EntityExtractionEvaluator` | `entity_med_precision`, `entity_med_recall`, `entity_med_f1`, `entity_symptom_precision`, `entity_symptom_recall`, `entity_symptom_f1` |
| `evaluators/format_validator.py` | `FormatValidator` | `format_score`, `format_errors`, `summary_length` |
| `evaluators/calibration.py` | `CalibrationEvaluator` | `confidence`, `is_correct`, `judge_score` |
| `evaluators/llm_judge.py` | `LLMJudgeEvaluator` | `llm_judge_score` |
| `evaluators/retrieval.py` | `RetrievalEvaluator` | `retrieval_precision@k`, `retrieval_recall@k`, `retrieval_f1@k`, `retrieval_mrr`, `retrieval_ndcg@k` |
| `evaluators/hallucination.py` | `HallucinationDetectorEvaluator` | `hallucination_detected`, `hallucination_score`, `hallucination_types`, `forbidden_facts_found`, `unsupported_medications`, `num_violations` |
| `evaluators/hallucination.py` | `FaithfulnessEvaluator` | `faithfulness_score`, `grounded_sentences`, `total_sentences`, `ungrounded_claims`, `num_ungrounded` |
| `evaluators/safety.py` | `PromptInjectionDetectorEvaluator` | `injection_detected`, `injection_score`, `injection_patterns`, `suspicious_phrases`, `output_leaked_instructions`, `model_rejected_attack`, `is_adversarial_input` |
| `evaluators/safety.py` | `AdversarialRobustnessEvaluator` | `robustness_score`, `consistency_with_baseline`, `passed_robustness_test`, `variation_type`, `degradation_signals`, `is_baseline` |
| `evaluators/safety.py` | `SafetyGuardEvaluator` | `safety_passed`, `safety_score`, `safety_violations`, `num_violations`, `requires_human_review` |
| `evaluators/performance.py` | `PerformanceEvaluator` | `latency_ms`, `cost_usd`, `tokens_used`, `passed_latency_sla`, `passed_cost_sla` |
| `evaluators/performance.py` | `ReliabilityEvaluator` | `prediction_succeeded`, `is_error`, `is_timeout`, `error_type`, `availability` |

Notes:

- The exported format checker class is **`FormatValidator`**.
- The LLM-judge protocol lives in **`src/medeval/llm_judge.py`**; the evaluator wrapper lives in **`src/medeval/evaluators/llm_judge.py`**.

## RAG evaluation example

```python
from medeval.evaluators import RetrievalEvaluator
from medeval.models import ClinicalCase, Prediction, RetrievedDocument

case = ClinicalCase(
    id="rag_001",
    text="Patient presents with acute chest pain radiating to the left arm.",
    symptoms=["chest pain", "dyspnea"],
    medications=["lisinopril", "atorvastatin"],
    required_facts=["cardiac"],
    forbidden_facts=[],
    gold_summary={"summary_text": "Likely acute coronary syndrome."},
    relevant_doc_ids=["cardio_guideline_001", "acs_protocol_2024", "chest_pain_diff_dx"],
)

prediction = Prediction(
    case_id="rag_001",
    summary_text="Likely acute coronary syndrome.",
    medications=[],
    retrieved_docs=[
        RetrievedDocument(doc_id="acs_protocol_2024", text="...", score=0.95, rank=1),
        RetrievedDocument(doc_id="cardio_guideline_001", text="...", score=0.89, rank=2),
    ],
)

result = RetrievalEvaluator(k=5).evaluate(case, prediction)
print(result["retrieval_precision@5"])
print(result["retrieval_recall@5"])
print(result["retrieval_mrr"])
print(result["retrieval_ndcg@5"])
```

## Judge-based evaluation and calibration

`src/medeval/llm_judge.py` defines the lightweight protocol that judge-based evaluators consume:

```python
from medeval.llm_judge import LLMJudge
from medeval.evaluators import LLMJudgeEvaluator, CalibrationEvaluator

class MyJudge:
    def judge(self, gold_text: str, pred_text: str) -> float:
        return 0.9

judge_eval = LLMJudgeEvaluator(llm_judge=MyJudge())
calibration_eval = CalibrationEvaluator(llm_judge=MyJudge(), threshold=0.7)
```

`CalibrationEvaluator` produces per-case `confidence`, `is_correct`, and `judge_score`. If you want dataset-level calibration error, use `medeval.evaluation.metrics.aggregate(...)`, which adds `calibration_ece` when those fields are present.

## Human evaluation, baselines, and statistics

Useful utility modules under `src/medeval/evaluation/`:

- `human_eval.py`
  - `HumanRating`
  - `HumanEvaluationWorkflow`
  - `format_inter_rater_reliability_report(...)`
- `baseline.py`
  - `load_baseline(path)`
- `quality_gate.py`
  - `evaluate_quality_gate(aggregated_metrics, baseline)`
- `statistics.py`
  - `ComparisonResult`
  - `StatisticalComparator`
  - `format_comparison_report(...)`
- `metrics.py`
  - `aggregate(case_level_results)`

Example baseline comparison:

```python
from medeval.evaluation.baseline import load_baseline
from medeval.evaluation.quality_gate import evaluate_quality_gate

baseline = load_baseline("baseline.json")
passed, failures = evaluate_quality_gate(results.aggregated_metrics, baseline)
```

Example statistical comparison:

```python
from medeval.evaluation.statistics import StatisticalComparator

baseline_scores = [0.85, 0.87, 0.84, 0.86]
candidate_scores = [0.88, 0.89, 0.87, 0.90]

comparison = StatisticalComparator(significance_level=0.05).compare_means(
    "med_f1",
    baseline_scores,
    candidate_scores,
)

print(comparison.percent_change)
print(comparison.confidence_interval_95)
print(comparison.p_value)
print(comparison.is_significant)
print(comparison.winner)
```

## Plugin system

Third-party evaluators can register under the `medeval.evaluators` entry-point group.

```python
from medeval.evaluators.base import Evaluator, discover_evaluators

class ClinicalSafetyEvaluator(Evaluator):
    def evaluate(self, case, prediction):
        return {"custom_safety_score": 0.95}

plugins = discover_evaluators()
```

Example `pyproject.toml` entry point:

```toml
[tool.poetry.plugins."medeval.evaluators"]
clinical_safety = "my_package.evaluators:ClinicalSafetyEvaluator"
```

## Project structure

```text
medeval/
├── AI_TESTING_HANDBOOK.html
├── README.md
├── examples/
│   ├── README.md
│   └── datasets/
│       ├── adversarial_cases.jsonl
│       ├── adversarial_predictions.jsonl
│       ├── hallucination_cases.jsonl
│       ├── hallucination_predictions_bad.jsonl
│       ├── rag_cases.jsonl
│       └── rag_predictions.jsonl
├── pyproject.toml
├── src/medeval/
│   ├── __init__.py
│   ├── dataset.py
│   ├── llm_judge.py
│   ├── models.py
│   ├── evaluation/
│   │   ├── baseline.py
│   │   ├── human_eval.py
│   │   ├── metrics.py
│   │   ├── quality_gate.py
│   │   ├── runner.py
│   │   └── statistics.py
│   └── evaluators/
│       ├── __init__.py
│       ├── base.py
│       ├── calibration.py
│       ├── entity_extraction.py
│       ├── forbidden_facts.py
│       ├── format_validator.py
│       ├── hallucination.py
│       ├── llm_judge.py
│       ├── medication_f1.py
│       ├── performance.py
│       ├── required_facts.py
│       ├── retrieval.py
│       └── safety.py
└── tests/
```

## Development

```bash
python -m pytest
python -m flake8 src tests
```

If you use Poetry dev dependencies instead:

```bash
poetry install
poetry run pytest
poetry run flake8 src tests
```

## CLI note

This repository does **not** provide the `medeval` CLI. If you want CLI-oriented workflows, use the separate **medevalHelpers** repository/package and treat this repo as the evaluation library it builds on.

## License

MIT
