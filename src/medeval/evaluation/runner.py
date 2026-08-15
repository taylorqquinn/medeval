"""Runner that executes the evaluation pipeline over a dataset."""

from typing import Optional, Dict, Any, List
from medeval.dataset import load_cases
from medeval.application.clinical_ai import ClinicalAI
from medeval.application.llm_client import LLMClient
from medeval.evaluators.required_facts import RequiredFactsEvaluator
from medeval.evaluators.forbidden_facts import ForbiddenFactsEvaluator
from medeval.evaluators.medication_f1 import MedicationF1Evaluator
from medeval.evaluators.llm_judge import LLMJudgeEvaluator
from medeval.evaluators.format_validator import FormatValidator
from medeval.evaluators.entity_extraction import EntityExtractionEvaluator
from medeval.evaluators.calibration import CalibrationEvaluator
from medeval.evaluation.metrics import aggregate
from medeval.evaluation.baseline import load_baseline
from medeval.evaluation.quality_gate import evaluate_quality_gate


def run(dataset_path: str, baseline_path: Optional[str] = None, llm_client: Optional[LLMClient] = None) -> Dict[str, Any]:
    """Run the evaluation pipeline and return a result dict."""
    cases = load_cases(dataset_path)
    # If the caller did not provide an LLM client, prefer OpenAIClient when an API key is present.
    if llm_client is None:
        try:
            import os as _os
            if _os.getenv("OPENAI_API_KEY"):
                from medeval.application.openai_client import OpenAIClient
                llm_client = OpenAIClient()
            else:
                llm_client = LLMClient()
        except Exception:
            # Fall back to the local deterministic client if OpenAI isn't available.
            llm_client = LLMClient()
    ai = ClinicalAI(llm_client=llm_client)
    evaluators = [
        RequiredFactsEvaluator(),
        ForbiddenFactsEvaluator(),
        FormatValidator(),
        MedicationF1Evaluator(),
        EntityExtractionEvaluator(),
        LLMJudgeEvaluator(llm_client),
        CalibrationEvaluator(llm_client)
    ]
    per_case_results: List[Dict[str, Any]] = []

    for case in cases:
        pred = ai.summarize(case)
        case_metrics = {}
        for ev in evaluators:
            res = ev.evaluate(case, pred)
            case_metrics.update(res)
        per_case_results.append(case_metrics)

    aggregated = aggregate(per_case_results)

    baseline = load_baseline(baseline_path) if baseline_path else {}
    if baseline:
        passed, failures = evaluate_quality_gate(aggregated, baseline)
    else:
        passed, failures = (None, [])

    return {"aggregated": aggregated, "passed": passed, "failures": failures, "per_case_results": per_case_results}
