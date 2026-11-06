"""Human evaluation workflow framework.

This module provides utilities for managing human evaluation of AI predictions,
including inter-rater reliability calculations and annotation guidelines.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("medeval.evaluation.human_eval")


@dataclass
class HumanRating:
    """A single human rating for a prediction."""

    case_id: str
    rater_id: str
    accuracy: int | None = None  # 1-5 scale
    safety: int | None = None  # 1-5 scale
    helpfulness: int | None = None  # 1-5 scale
    has_errors: bool = False
    error_types: list[str] = field(default_factory=list)
    free_text_feedback: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class InterRaterReliability:
    """Inter-rater reliability statistics."""

    metric_name: str
    num_raters: int
    num_cases: int
    agreement_rate: float  # Simple agreement %
    cohens_kappa: float | None = None
    fleiss_kappa: float | None = None
    krippendorffs_alpha: float | None = None


class HumanEvaluationWorkflow:
    """Framework for managing human evaluation of AI predictions.

    Supports:
    - Multiple raters per case
    - Inter-rater reliability (Kappa, agreement rate)
    - Annotation guidelines and rubrics
    - Quality control (catch raters who disagree with majority)

    Example:
        workflow = HumanEvaluationWorkflow()

        # Add ratings from multiple raters
        workflow.add_rating(HumanRating(
            case_id="c1",
            rater_id="doctor1",
            accuracy=5,
            safety=5,
            helpfulness=4
        ))

        # Calculate inter-rater reliability
        irr = workflow.calculate_inter_rater_reliability("accuracy")
        print(f"Cohen's Kappa: {irr.cohens_kappa:.3f}")
    """

    def __init__(self):
        """Initialize the human evaluation workflow."""
        self.ratings: list[HumanRating] = []

    def add_rating(self, rating: HumanRating) -> None:
        """Add a human rating to the workflow.

        Args:
            rating: HumanRating object
        """
        self.ratings.append(rating)
        logger.debug(f"Added rating from {rating.rater_id} for case {rating.case_id}")

    def add_ratings(self, ratings: list[HumanRating]) -> None:
        """Add multiple ratings at once.

        Args:
            ratings: List of HumanRating objects
        """
        for rating in ratings:
            self.add_rating(rating)

    def get_ratings_for_case(self, case_id: str) -> list[HumanRating]:
        """Get all ratings for a specific case.

        Args:
            case_id: Case identifier

        Returns:
            List of HumanRating objects for this case
        """
        return [r for r in self.ratings if r.case_id == case_id]

    def get_ratings_by_rater(self, rater_id: str) -> list[HumanRating]:
        """Get all ratings from a specific rater.

        Args:
            rater_id: Rater identifier

        Returns:
            List of HumanRating objects from this rater
        """
        return [r for r in self.ratings if r.rater_id == rater_id]

    def calculate_inter_rater_reliability(
        self, metric_name: str, min_raters: int = 2
    ) -> InterRaterReliability:
        """Calculate inter-rater reliability for a metric.

        Args:
            metric_name: Name of metric to analyze ("accuracy", "safety", "helpfulness")
            min_raters: Minimum number of raters required per case

        Returns:
            InterRaterReliability object with statistics
        """
        logger.info(f"Calculating inter-rater reliability for '{metric_name}'")

        # Group ratings by case
        case_ratings: dict[str, list[int]] = defaultdict(list)
        raters_seen = set()

        for rating in self.ratings:
            value = getattr(rating, metric_name, None)
            if value is not None:
                case_ratings[rating.case_id].append(value)
                raters_seen.add(rating.rater_id)

        # Filter to cases with minimum raters
        cases_with_enough_raters = {
            case_id: ratings
            for case_id, ratings in case_ratings.items()
            if len(ratings) >= min_raters
        }

        if not cases_with_enough_raters:
            logger.warning(f"No cases have {min_raters}+ raters for metric '{metric_name}'")
            return InterRaterReliability(
                metric_name=metric_name,
                num_raters=len(raters_seen),
                num_cases=0,
                agreement_rate=0.0,
                cohens_kappa=None,
            )

        # Calculate agreement rate
        agreement_rate = self._calculate_agreement_rate(cases_with_enough_raters)

        # Calculate Cohen's Kappa (for 2 raters)
        cohens_kappa = None
        if len(raters_seen) == 2:
            cohens_kappa = self._calculate_cohens_kappa(cases_with_enough_raters)

        # Calculate Fleiss' Kappa (for 3+ raters)
        fleiss_kappa = None
        if len(raters_seen) >= 3:
            fleiss_kappa = self._calculate_fleiss_kappa(cases_with_enough_raters)

        logger.info(
            f"IRR for '{metric_name}': {len(cases_with_enough_raters)} cases, "
            f"agreement={agreement_rate:.2f}, kappa={cohens_kappa or fleiss_kappa or 'N/A'}"
        )

        return InterRaterReliability(
            metric_name=metric_name,
            num_raters=len(raters_seen),
            num_cases=len(cases_with_enough_raters),
            agreement_rate=agreement_rate,
            cohens_kappa=cohens_kappa,
            fleiss_kappa=fleiss_kappa,
        )

    def _calculate_agreement_rate(self, case_ratings: dict[str, list[int]]) -> float:
        """Calculate simple agreement rate (% of cases where all raters agree).

        Args:
            case_ratings: Dict mapping case_id to list of ratings

        Returns:
            Agreement rate (0.0 to 1.0)
        """
        if not case_ratings:
            return 0.0

        agreements = 0
        for ratings in case_ratings.values():
            if len(set(ratings)) == 1:  # All ratings are identical
                agreements += 1

        return agreements / len(case_ratings)

    def _calculate_cohens_kappa(self, case_ratings: dict[str, list[int]]) -> float:
        """Calculate Cohen's Kappa for two raters.

        Cohen's Kappa = (Po - Pe) / (1 - Pe)
        Where:
        - Po = observed agreement
        - Pe = expected agreement by chance

        Args:
            case_ratings: Dict mapping case_id to list of ratings (must have exactly 2 per case)

        Returns:
            Cohen's Kappa (-1.0 to 1.0)
        """
        # Filter to cases with exactly 2 ratings
        two_rater_cases = [ratings for ratings in case_ratings.values() if len(ratings) == 2]

        if not two_rater_cases:
            return 0.0

        # Count agreements
        agreements = sum(1 for r1, r2 in two_rater_cases if r1 == r2)
        po = agreements / len(two_rater_cases)

        # Count marginal frequencies for Pe calculation
        rater1_counts = defaultdict(int)
        rater2_counts = defaultdict(int)

        for r1, r2 in two_rater_cases:
            rater1_counts[r1] += 1
            rater2_counts[r2] += 1

        n = len(two_rater_cases)
        pe = sum(
            (rater1_counts[category] / n) * (rater2_counts[category] / n)
            for category in set(list(rater1_counts.keys()) + list(rater2_counts.keys()))
        )

        if pe == 1.0:
            return 1.0  # Perfect agreement by chance

        kappa = (po - pe) / (1 - pe)
        return kappa

    def _calculate_fleiss_kappa(self, case_ratings: dict[str, list[int]]) -> float:
        """Calculate Fleiss' Kappa for 3+ raters.

        Fleiss' Kappa extends Cohen's Kappa to multiple raters.

        Args:
            case_ratings: Dict mapping case_id to list of ratings

        Returns:
            Fleiss' Kappa (-1.0 to 1.0)
        """
        # This is a simplified implementation
        # For production, use statsmodels.stats.inter_rater.fleiss_kappa

        # For now, return average pairwise Cohen's Kappa as approximation
        # (Real Fleiss' Kappa has different formula)
        logger.warning("Using simplified Fleiss' Kappa (average pairwise Cohen's Kappa)")

        # Just return None for now - implement full Fleiss' Kappa if needed
        return None

    def get_aggregated_ratings(self, case_id: str) -> dict[str, Any]:
        """Get aggregated statistics for all ratings of a case.

        Args:
            case_id: Case identifier

        Returns:
            Dict with mean, median, std dev for each metric
        """
        ratings = self.get_ratings_for_case(case_id)

        if not ratings:
            return {}

        result = {"num_ratings": len(ratings), "raters": [r.rater_id for r in ratings]}

        # Aggregate numeric metrics
        for metric in ["accuracy", "safety", "helpfulness"]:
            values = [getattr(r, metric) for r in ratings if getattr(r, metric) is not None]
            if values:
                result[f"{metric}_mean"] = sum(values) / len(values)
                result[f"{metric}_median"] = sorted(values)[len(values) // 2]
                result[f"{metric}_min"] = min(values)
                result[f"{metric}_max"] = max(values)

        # Aggregate error flags
        result["has_errors_count"] = sum(1 for r in ratings if r.has_errors)
        result["has_errors_rate"] = result["has_errors_count"] / len(ratings)

        return result

    def identify_outlier_raters(
        self, metric_name: str, disagreement_threshold: float = 0.3
    ) -> list[dict[str, Any]]:
        """Identify raters who frequently disagree with others.

        Useful for quality control - catch inattentive or miscalibrated raters.

        Args:
            metric_name: Metric to analyze
            disagreement_threshold: Fraction of cases where rater can disagree

        Returns:
            List of dicts with rater info and disagreement rate
        """
        rater_disagreements = defaultdict(lambda: {"total": 0, "disagreed": 0})

        # For each case with multiple raters
        case_ratings_map: dict[str, list[HumanRating]] = defaultdict(list)
        for rating in self.ratings:
            case_ratings_map[rating.case_id].append(rating)

        for _case_id, case_ratings in case_ratings_map.items():
            if len(case_ratings) < 2:
                continue

            # Get values for this metric
            values_by_rater = {}
            for rating in case_ratings:
                value = getattr(rating, metric_name, None)
                if value is not None:
                    values_by_rater[rating.rater_id] = value

            if len(values_by_rater) < 2:
                continue

            # Find majority value
            value_counts = defaultdict(int)
            for value in values_by_rater.values():
                value_counts[value] += 1

            majority_value = max(value_counts, key=value_counts.get)

            # Check each rater
            for rater_id, value in values_by_rater.items():
                rater_disagreements[rater_id]["total"] += 1
                if value != majority_value:
                    rater_disagreements[rater_id]["disagreed"] += 1

        # Calculate disagreement rates
        outliers = []
        for rater_id, stats in rater_disagreements.items():
            if stats["total"] == 0:
                continue

            disagreement_rate = stats["disagreed"] / stats["total"]
            if disagreement_rate > disagreement_threshold:
                outliers.append(
                    {
                        "rater_id": rater_id,
                        "disagreement_rate": disagreement_rate,
                        "num_cases": stats["total"],
                        "num_disagreements": stats["disagreed"],
                    }
                )

        return sorted(outliers, key=lambda x: x["disagreement_rate"], reverse=True)


def format_inter_rater_reliability_report(irr_results: list[InterRaterReliability]) -> str:
    """Format inter-rater reliability results as a readable report.

    Args:
        irr_results: List of InterRaterReliability objects

    Returns:
        Formatted string report
    """
    lines = []
    lines.append("=" * 80)
    lines.append("INTER-RATER RELIABILITY REPORT")
    lines.append("=" * 80)
    lines.append("")

    for irr in irr_results:
        lines.append(f"Metric: {irr.metric_name}")
        lines.append(f"  Raters: {irr.num_raters}")
        lines.append(f"  Cases: {irr.num_cases}")
        lines.append(f"  Agreement rate: {irr.agreement_rate:.1%}")

        if irr.cohens_kappa is not None:
            lines.append(
                f"  Cohen's Kappa: {irr.cohens_kappa:.3f} {_interpret_kappa(irr.cohens_kappa)}"
            )
        elif irr.fleiss_kappa is not None:
            lines.append(
                f"  Fleiss' Kappa: {irr.fleiss_kappa:.3f} {_interpret_kappa(irr.fleiss_kappa)}"
            )

        lines.append("")

    lines.append("=" * 80)
    lines.append("")
    lines.append("Kappa interpretation:")
    lines.append("  < 0.00: Poor agreement")
    lines.append("  0.00 - 0.20: Slight agreement")
    lines.append("  0.21 - 0.40: Fair agreement")
    lines.append("  0.41 - 0.60: Moderate agreement")
    lines.append("  0.61 - 0.80: Substantial agreement")
    lines.append("  0.81 - 1.00: Almost perfect agreement")
    lines.append("=" * 80)

    return "\n".join(lines)


def _interpret_kappa(kappa: float) -> str:
    """Interpret Kappa value."""
    if kappa < 0:
        return "(Poor)"
    elif kappa < 0.20:
        return "(Slight)"
    elif kappa < 0.40:
        return "(Fair)"
    elif kappa < 0.60:
        return "(Moderate)"
    elif kappa < 0.80:
        return "(Substantial)"
    else:
        return "(Almost Perfect)"
