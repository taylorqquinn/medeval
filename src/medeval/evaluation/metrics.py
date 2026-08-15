"""Aggregation helpers for evaluator outputs."""

from typing import List, Dict, Any
import numbers

def aggregate(case_level_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate per-case evaluator outputs into dataset-level metrics.

    Numeric metrics are averaged; lists are concatenated.
    """
    sums = {}
    counts = {}
    lists = {}

    for res in case_level_results:
        for k, v in res.items():
            if isinstance(v, numbers.Number):
                sums[k] = sums.get(k, 0.0) + float(v)
                counts[k] = counts.get(k, 0) + 1
            else:
                # treat non-numeric (lists, dicts) as lists to concatenate
                lists.setdefault(k, []).extend(v if isinstance(v, list) else [v])

    aggregated = {}
    for k, total in sums.items():
        aggregated[k] = total / counts[k] if counts.get(k) else None
    for k, items in lists.items():
        aggregated[k] = items

    # dataset-level calibration: if per-case confidences and correctness are present,
    # compute expected calibration error (ECE) using 10 bins.
    confidences = []
    correctness = []
    for res in case_level_results:
        if 'confidence' in res and 'is_correct' in res:
            try:
                confidences.append(float(res['confidence']))
                correctness.append(1.0 if res['is_correct'] else 0.0)
            except Exception:
                continue

    def _compute_ece(confidences_list, correctness_list, n_bins=10):
        if not confidences_list:
            return None
        total = len(confidences_list)
        ece = 0.0
        for i in range(n_bins):
            lower = i / n_bins
            upper = (i + 1) / n_bins
            idxs = [j for j, c in enumerate(confidences_list) if (c >= lower and c < upper) or (i == n_bins - 1 and c <= upper)]
            if not idxs:
                continue
            avg_conf = sum(confidences_list[j] for j in idxs) / len(idxs)
            acc = sum(correctness_list[j] for j in idxs) / len(idxs)
            ece += (len(idxs) / total) * abs(avg_conf - acc)
        return ece

    ece = _compute_ece(confidences, correctness, n_bins=10)
    if ece is not None:
        aggregated['calibration_ece'] = ece

    return aggregated
