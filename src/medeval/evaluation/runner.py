"""Runner that executes the evaluation pipeline over a dataset."""

import logging
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
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

logger = logging.getLogger('medeval.runner')


def run(dataset_path: str, baseline_path: Optional[str] = None, 
        llm_client: Optional[LLMClient] = None,
        save_artifacts: bool = True,
        artifacts_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Run the evaluation pipeline and return a result dict.
    
    Args:
        dataset_path: Path to dataset JSONL file.
        baseline_path: Optional path to baseline JSON file.
        llm_client: Optional LLM client instance.
        save_artifacts: Whether to save artifacts (predictions, metrics).
        artifacts_dir: Optional directory to save artifacts.
    
    Returns:
        Dictionary with keys: aggregated, passed, failures, per_case_results.
        
    Raises:
        FileNotFoundError: If dataset or baseline file not found.
        ValueError: If dataset is empty or invalid.
        RuntimeError: If evaluation pipeline fails.
    """
    logger.info("="*60)
    logger.info("Starting evaluation pipeline")
    logger.info(f"Dataset: {dataset_path}")
    logger.info(f"Baseline: {baseline_path or 'None'}")
    logger.info("="*60)
    
    # Validate inputs
    if not Path(dataset_path).exists():
        error_msg = f"Dataset file not found: {dataset_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    if baseline_path and not Path(baseline_path).exists():
        error_msg = f"Baseline file not found: {baseline_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    # Load dataset
    logger.info(f"Loading cases from {dataset_path}...")
    try:
        cases = load_cases(dataset_path)
    except Exception as e:
        error_msg = f"Failed to load dataset from {dataset_path}: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e
    
    if not cases:
        error_msg = f"Dataset is empty: {dataset_path}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Loaded {len(cases)} case(s)")
    
    # Initialize LLM client
    if llm_client is None:
        logger.info("No LLM client provided, selecting default...")
        try:
            import os as _os
            if _os.getenv("OPENAI_API_KEY"):
                logger.info("OpenAI API key found, using OpenAIClient")
                from medeval.application.openai_client import OpenAIClient
                llm_client = OpenAIClient()
            else:
                logger.info("No OpenAI API key, using deterministic LLMClient")
                llm_client = LLMClient()
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client: {e}")
            logger.info("Falling back to deterministic LLMClient")
            llm_client = LLMClient()
    else:
        logger.info(f"Using provided LLM client: {type(llm_client).__name__}")
    
    # Initialize AI and evaluators
    logger.info("Initializing ClinicalAI and evaluators...")
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
    logger.info(f"Initialized {len(evaluators)} evaluator(s)")
    
    # Process cases
    per_case_results: List[Dict[str, Any]] = []
    failed_cases: List[str] = []
    logger.info("Processing cases...")
    
    for i, case in enumerate(cases, 1):
        logger.debug(f"Processing case {i}/{len(cases)}: {case.id}")
        
        try:
            # Generate prediction
            pred = ai.summarize(case)
            logger.debug(f"  Generated summary ({len(pred.summary_text)} chars, {len(pred.medications)} meds)")
            
            # Run evaluators
            case_metrics = {}
            for ev in evaluators:
                ev_name = type(ev).__name__
                logger.debug(f"  Running evaluator: {ev_name}")
                try:
                    res = ev.evaluate(case, pred)
                    case_metrics.update(res)
                except Exception as ev_error:
                    logger.error(f"  Evaluator {ev_name} failed for case {case.id}: {ev_error}")
                    # Continue with other evaluators
            
            per_case_results.append(case_metrics)
            logger.info(f"Completed case {i}/{len(cases)}: {case.id}")
            
        except Exception as case_error:
            logger.error(f"Failed to process case {case.id}: {case_error}")
            failed_cases.append(case.id)
            # Continue with next case
    
    if failed_cases:
        logger.warning(f"Failed to process {len(failed_cases)} case(s): {failed_cases}")
    
    if not per_case_results:
        error_msg = "No cases were successfully processed"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info(f"Successfully processed {len(per_case_results)}/{len(cases)} case(s)")
    
    # Save predictions if requested
    if save_artifacts and artifacts_dir:
        try:
            pred_file = artifacts_dir / "predictions.json"
            with open(pred_file, 'w', encoding='utf-8') as fh:
                json.dump(per_case_results, fh, indent=2)
            logger.info(f"Predictions saved to: {pred_file}")
        except Exception as e:
            logger.error(f"Failed to save predictions: {e}")
    
    # Aggregate metrics
    logger.info("Aggregating metrics...")
    aggregated = aggregate(per_case_results)
    logger.info(f"Computed {len(aggregated)} aggregated metric(s)")
    
    # Save aggregated metrics if requested
    if save_artifacts and artifacts_dir:
        try:
            metrics_file = artifacts_dir / "aggregated_metrics.json"
            with open(metrics_file, 'w', encoding='utf-8') as fh:
                json.dump(aggregated, fh, indent=2)
            logger.info(f"Aggregated metrics saved to: {metrics_file}")
        except Exception as e:
            logger.error(f"Failed to save aggregated metrics: {e}")
    
    # Quality gate evaluation
    baseline = load_baseline(baseline_path) if baseline_path else {}
    if baseline:
        logger.info(f"Evaluating quality gate with {len(baseline)} threshold(s)...")
        passed, failures = evaluate_quality_gate(aggregated, baseline)
        logger.info(f"Quality gate: {'PASSED' if passed else 'FAILED'}")
        if failures:
            logger.warning(f"Quality gate failures ({len(failures)}):")
            for failure in failures:
                logger.warning(f"  - {failure}")
    else:
        logger.info("No baseline provided, skipping quality gate evaluation")
        passed, failures = (None, [])
    
    # Save quality gate results if requested
    if save_artifacts and artifacts_dir and baseline:
        try:
            qg_file = artifacts_dir / "quality_gate.json"
            qg_result = {'passed': passed, 'failures': failures, 'baseline': baseline}
            with open(qg_file, 'w', encoding='utf-8') as fh:
                json.dump(qg_result, fh, indent=2)
            logger.info(f"Quality gate results saved to: {qg_file}")
        except Exception as e:
            logger.error(f"Failed to save quality gate results: {e}")
    
    # Save cost report if using OpenAI client with cost tracking
    if save_artifacts and artifacts_dir and llm_client:
        try:
            # Check if this is an OpenAI client with cost tracking
            if hasattr(llm_client, 'get_cost_report'):
                cost_report = llm_client.get_cost_report()
                if cost_report:
                    cost_file = artifacts_dir / "cost_report.json"
                    with open(cost_file, 'w', encoding='utf-8') as fh:
                        json.dump(cost_report, fh, indent=2)
                    logger.info(f"Cost report saved to: {cost_file}")
                    logger.info(f"Total API cost: ${cost_report.get('total_cost_usd', 0):.6f}")
        except Exception as e:
            logger.error(f"Failed to save cost report: {e}")
    
    logger.info("="*60)
    logger.info("Evaluation pipeline completed")
    logger.info("="*60)
    
    return {"aggregated": aggregated, "passed": passed, "failures": failures, "per_case_results": per_case_results}
