"""Dataset loading utilities."""

import json
import logging

from medeval.models import ClinicalCase

logger = logging.getLogger("medeval.dataset")


def load_cases(path: str) -> list[ClinicalCase]:
    """Load clinical cases from a JSONL file.

    Args:
        path: Path to JSONL file containing clinical cases.

    Returns:
        List of ClinicalCase objects.

    Raises:
        FileNotFoundError: If path does not exist.
        json.JSONDecodeError: If file contains invalid JSON.
    """
    logger.debug(f"Loading cases from: {path}")
    cases: list[ClinicalCase] = []

    try:
        with open(path, encoding="utf-8") as fh:
            line_num = 0
            for line in fh:
                line_num += 1
                line = line.strip()
                if not line:
                    logger.debug(f"Skipping empty line {line_num}")
                    continue

                try:
                    j = json.loads(line)
                    case = ClinicalCase(
                        id=str(j.get("id", "")),
                        text=j.get("text", ""),
                        symptoms=j.get("symptoms", []),
                        medications=j.get("medications", []),
                        required_facts=j.get("required_facts", []),
                        forbidden_facts=j.get("forbidden_facts", []),
                        gold_summary=j.get("gold_summary", {}),
                    )
                    cases.append(case)
                    logger.debug(f"Loaded case {case.id} (line {line_num})")
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON on line {line_num}: {e}")
                    raise

        logger.info(f"Successfully loaded {len(cases)} case(s) from {path}")
        return cases

    except FileNotFoundError:
        logger.error(f"Dataset file not found: {path}")
        raise
    except Exception as e:
        logger.error(f"Failed to load dataset from {path}: {e}")
        raise


# Alias for convenience
load_dataset = load_cases
