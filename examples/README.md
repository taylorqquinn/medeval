# MedEval Examples

This directory contains runnable examples demonstrating all MedEval evaluators.

## Directory Structure

```
examples/
├── datasets/              # Test datasets in JSONL format
│   ├── rag_cases.jsonl               # RAG system test cases
│   ├── rag_predictions.jsonl         # Example RAG predictions
│   ├── hallucination_cases.jsonl     # Hallucination detection cases
│   ├── hallucination_predictions_bad.jsonl  # Examples with hallucinations
│   ├── adversarial_cases.jsonl       # Adversarial/security test cases
│   └── adversarial_predictions.jsonl # Model responses to attacks
└── README.md             # This file
```

## Quick Start

### 1. Run RAG Evaluation

```python
import json
from medeval.models import ClinicalCase, Prediction
from medeval.evaluators import RetrievalEvaluator
from medeval.dataset import load_cases

# Load test cases
cases = load_cases("examples/datasets/rag_cases.jsonl")

# Load predictions
with open("examples/datasets/rag_predictions.jsonl") as f:
    predictions = [Prediction(**json.loads(line)) for line in f]

# Evaluate retrieval quality
evaluator = RetrievalEvaluator(k=5)
for case, prediction in zip(cases, predictions):
    result = evaluator.evaluate(case, prediction)
    print(f"\nCase {case.id}:")
    print(f"  Precision@5: {result['retrieval_precision@5']:.2f}")
    print(f"  Recall@5: {result['retrieval_recall@5']:.2f}")
    print(f"  MRR: {result['retrieval_mrr']:.2f}")
    print(f"  NDCG@5: {result['retrieval_ndcg@5']:.2f}")
```

### 2. Run Hallucination Detection

```python
from medeval.evaluators import HallucinationDetectorEvaluator, FaithfulnessEvaluator
from medeval.dataset import load_cases
import json

# Load cases and bad predictions
cases = load_cases("examples/datasets/hallucination_cases.jsonl")

with open("examples/datasets/hallucination_predictions_bad.jsonl") as f:
    predictions = [Prediction(**json.loads(line)) for line in f]

# Detect hallucinations
hallucination_eval = HallucinationDetectorEvaluator(strict_mode=True)
faithfulness_eval = FaithfulnessEvaluator()

for case, prediction in zip(cases, predictions):
    hall_result = hallucination_eval.evaluate(case, prediction)
    faith_result = faithfulness_eval.evaluate(case, prediction)
    
    print(f"\nCase {case.id}:")
    print(f"  Hallucination detected: {hall_result['hallucination_detected']}")
    print(f"  Hallucination score: {hall_result['hallucination_score']:.2f}")
    print(f"  Forbidden facts found: {hall_result['forbidden_facts_found']}")
    print(f"  Faithfulness score: {faith_result['faithfulness_score']:.2f}")
```

### 3. Run Security Testing

```python
from medeval.evaluators import PromptInjectionDetectorEvaluator, SafetyGuardEvaluator
from medeval.dataset import load_cases
import json

# Load adversarial cases
cases = load_cases("examples/datasets/adversarial_cases.jsonl")

with open("examples/datasets/adversarial_predictions.jsonl") as f:
    predictions = [Prediction(**json.loads(line)) for line in f]

# Test security
injection_eval = PromptInjectionDetectorEvaluator()
safety_eval = SafetyGuardEvaluator()

for case, prediction in zip(cases, predictions):
    injection_result = injection_eval.evaluate(case, prediction)
    safety_result = safety_eval.evaluate(case, prediction)
    
    print(f"\nCase {case.id}:")
    print(f"  Injection detected: {injection_result['injection_detected']}")
    print(f"  Model rejected attack: {injection_result['model_rejected_attack']}")
    print(f"  Safety passed: {safety_result['safety_passed']}")
```

## Dataset Descriptions

### RAG Cases (rag_cases.jsonl)
- 3 clinical cases with ground truth relevant documents
- Tests retrieval quality (precision@k, recall@k, MRR, NDCG)
- Cases: cardiac emergency, infection, meningitis

### Hallucination Cases (hallucination_cases.jsonl)
- 2 cases with mild symptoms
- Contains forbidden facts (e.g., "definitely cancer", "terminal")
- Tests hallucination detection and faithfulness

### Adversarial Cases (adversarial_cases.jsonl)
- 2 prompt injection attempts
- 1 typo perturbation case
- Tests security and robustness

## Running Complete Evaluation

```python
from medeval.evaluation.runner import EvaluationRunner
from medeval.evaluators import *
from medeval.dataset import load_cases
import json

# Load all cases
all_cases = (
    load_cases("examples/datasets/rag_cases.jsonl") +
    load_cases("examples/datasets/hallucination_cases.jsonl") +
    load_cases("examples/datasets/adversarial_cases.jsonl")
)

# Load all predictions (merge JSONL files)
all_predictions = []
for pred_file in ["rag_predictions.jsonl", "hallucination_predictions_bad.jsonl", "adversarial_predictions.jsonl"]:
    with open(f"examples/datasets/{pred_file}") as f:
        all_predictions.extend([Prediction(**json.loads(line)) for line in f])

# Run comprehensive evaluation
runner = EvaluationRunner(
    evaluators=[
        MedicationF1Evaluator(),
        RequiredFactsEvaluator(),
        RetrievalEvaluator(k=5),
        HallucinationDetectorEvaluator(strict_mode=True),
        FaithfulnessEvaluator(),
        PromptInjectionDetectorEvaluator(),
        SafetyGuardEvaluator(),
        PerformanceEvaluator(latency_sla_ms=500.0),
        ReliabilityEvaluator(),
    ]
)

results = runner.run(all_cases, all_predictions)

# Print summary
print("\n=== EVALUATION SUMMARY ===")
for metric, value in results.aggregated_metrics.items():
    if isinstance(value, (int, float)):
        print(f"{metric}: {value:.3f}")
```

## Expected Results

When running the examples, you should see:

### RAG Cases
- ✅ **Good retrieval**: High precision@5, recall@5, MRR
- ✅ **Relevant docs at top**: NDCG@5 > 0.8

### Hallucination Cases (Bad Predictions)
- ❌ **Hallucinations detected**: forbidden facts found
- ❌ **Low faithfulness**: unsupported claims
- ❌ **Safety violations**: dangerous advice

### Adversarial Cases
- ✅ **Injection detected**: patterns identified
- ✅ **Model rejects attacks**: "I cannot comply..."
- ✅ **Robust to typos**: handles perturbations well

## Custom Datasets

To create your own test dataset:

1. **Create cases** (JSONL format):
```json
{"id": "custom_001", "text": "Your case text...", "symptoms": [...], "medications": [...], "required_facts": [...], "forbidden_facts": [...], "gold_summary": {...}}
```

2. **Generate predictions** from your AI model

3. **Run evaluation** using the examples above

## Next Steps

1. **Read `README.md`** - Concise API and architecture reference for the framework
2. **Read `AI_TESTING_HANDBOOK.html`** - End-to-end learning guide to the concepts and their implementation here
3. **Build your own datasets** - Adapt the sample JSONL structure to your domain
4. **Integrate into CI/CD** - Automate evaluation and quality gates

---

**Questions?** See main README.md or open an issue on GitHub.
