"""RAG retrieval quality evaluators.

This module provides evaluators for assessing the quality of document retrieval
in Retrieval-Augmented Generation (RAG) systems. Metrics include precision@k,
recall@k, Mean Reciprocal Rank (MRR), and Normalized Discounted Cumulative Gain (NDCG).
"""

import logging
import math
from typing import Any

from medeval.evaluators.base import Evaluator
from medeval.models import ClinicalCase, Prediction

logger = logging.getLogger("medeval.evaluators.retrieval")


class RetrievalEvaluator(Evaluator):
    """Evaluator for RAG retrieval quality metrics.

    Assesses how well the retrieval component of a RAG system identifies
    relevant documents. Requires:
    - ClinicalCase.relevant_doc_ids: list of ground truth relevant document IDs
    - Prediction.retrieved_docs: list of RetrievedDocument objects

    Computes:
    - precision@k: fraction of retrieved docs that are relevant
    - recall@k: fraction of relevant docs that were retrieved
    - MRR (Mean Reciprocal Rank): 1/rank of first relevant doc
    - NDCG@k (Normalized Discounted Cumulative Gain): ranking quality metric

    Example:
        Ground truth relevant docs: ["doc1", "doc3", "doc5"]
        Retrieved (top 5): ["doc1", "doc2", "doc3", "doc7", "doc9"]

        precision@5 = 2/5 = 0.4  (doc1, doc3 are relevant)
        recall@5 = 2/3 = 0.67  (found doc1, doc3 but missed doc5)
        MRR = 1/1 = 1.0  (first relevant doc at rank 1)
    """

    def __init__(self, k: int = 5):
        """Initialize the retrieval evaluator.

        Args:
            k: Number of top documents to consider for precision/recall/NDCG
        """
        super().__init__()
        self.k = k

    def evaluate(self, case: ClinicalCase, prediction: Prediction) -> dict[str, Any]:
        """Evaluate retrieval quality for a single case.

        Args:
            case: ClinicalCase with relevant_doc_ids field
            prediction: Prediction with retrieved_docs field

        Returns:
            Dictionary with keys:
              - retrieval_precision@k: float
              - retrieval_recall@k: float
              - retrieval_f1@k: float
              - retrieval_mrr: float
              - retrieval_ndcg@k: float
              - num_relevant_retrieved: int
              - num_retrieved: int
              - num_relevant_total: int
        """
        logger.debug(f"Evaluating retrieval quality for case {case.id}")

        # Handle missing data
        if not case.relevant_doc_ids:
            logger.warning(f"Case {case.id} has no relevant_doc_ids, skipping retrieval eval")
            return self._empty_result()

        if not prediction.retrieved_docs:
            logger.warning(f"Prediction for {case.id} has no retrieved_docs")
            return self._zero_result(len(case.relevant_doc_ids))

        # Extract relevant doc IDs
        relevant_set: set[str] = set(case.relevant_doc_ids)

        # Extract top-k retrieved doc IDs (sorted by rank)
        retrieved_docs = sorted(prediction.retrieved_docs, key=lambda d: d.rank)[: self.k]
        retrieved_ids = [doc.doc_id for doc in retrieved_docs]

        logger.debug(f"Relevant docs: {relevant_set}")
        logger.debug(f"Retrieved docs (top {self.k}): {retrieved_ids}")

        # Calculate metrics
        precision = self._precision_at_k(relevant_set, retrieved_ids)
        recall = self._recall_at_k(relevant_set, retrieved_ids)
        f1 = self._f1_score(precision, recall)
        mrr = self._mean_reciprocal_rank(relevant_set, retrieved_ids)
        ndcg = self._ndcg_at_k(relevant_set, retrieved_ids)

        num_relevant_retrieved = len([rid for rid in retrieved_ids if rid in relevant_set])

        logger.debug(
            f"Precision@{self.k}={precision:.3f}, Recall@{self.k}={recall:.3f}, "
            f"F1@{self.k}={f1:.3f}, MRR={mrr:.3f}, NDCG@{self.k}={ndcg:.3f}"
        )

        return {
            f"retrieval_precision@{self.k}": precision,
            f"retrieval_recall@{self.k}": recall,
            f"retrieval_f1@{self.k}": f1,
            "retrieval_mrr": mrr,
            f"retrieval_ndcg@{self.k}": ndcg,
            "num_relevant_retrieved": num_relevant_retrieved,
            "num_retrieved": len(retrieved_ids),
            "num_relevant_total": len(relevant_set),
        }

    def _precision_at_k(self, relevant: set[str], retrieved: list) -> float:
        """Calculate precision@k.

        Precision = (# relevant docs in top-k) / k
        """
        if not retrieved:
            return 0.0
        relevant_retrieved = sum(1 for doc_id in retrieved if doc_id in relevant)
        return relevant_retrieved / len(retrieved)

    def _recall_at_k(self, relevant: set[str], retrieved: list) -> float:
        """Calculate recall@k.

        Recall = (# relevant docs in top-k) / (total # relevant docs)
        """
        if not relevant:
            return 1.0  # No relevant docs to retrieve
        relevant_retrieved = sum(1 for doc_id in retrieved if doc_id in relevant)
        return relevant_retrieved / len(relevant)

    def _f1_score(self, precision: float, recall: float) -> float:
        """Calculate F1 score from precision and recall."""
        if precision + recall == 0:
            return 0.0
        return 2 * precision * recall / (precision + recall)

    def _mean_reciprocal_rank(self, relevant: set[str], retrieved: list) -> float:
        """Calculate Mean Reciprocal Rank (MRR).

        MRR = 1 / (rank of first relevant document)
        Returns 0.0 if no relevant documents found.
        """
        for rank, doc_id in enumerate(retrieved, start=1):
            if doc_id in relevant:
                return 1.0 / rank
        return 0.0

    def _ndcg_at_k(self, relevant: set[str], retrieved: list) -> float:
        """Calculate Normalized Discounted Cumulative Gain (NDCG@k).

        NDCG measures ranking quality, giving higher weight to relevant docs
        appearing earlier in the list.

        DCG = sum(relevance[i] / log2(i+1)) for i in 1..k
        NDCG = DCG / IDCG (ideal DCG with perfect ranking)
        """
        if not retrieved or not relevant:
            return 0.0

        # Calculate DCG (actual ranking)
        dcg = 0.0
        for rank, doc_id in enumerate(retrieved, start=1):
            relevance = 1.0 if doc_id in relevant else 0.0
            dcg += relevance / math.log2(rank + 1)

        # Calculate IDCG (ideal ranking - all relevant docs first)
        num_relevant = min(len(relevant), len(retrieved))
        idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, num_relevant + 1))

        if idcg == 0:
            return 0.0

        return dcg / idcg

    def _empty_result(self) -> dict[str, Any]:
        """Return empty result when evaluation cannot be performed."""
        return {
            f"retrieval_precision@{self.k}": None,
            f"retrieval_recall@{self.k}": None,
            f"retrieval_f1@{self.k}": None,
            "retrieval_mrr": None,
            f"retrieval_ndcg@{self.k}": None,
            "num_relevant_retrieved": 0,
            "num_retrieved": 0,
            "num_relevant_total": 0,
        }

    def _zero_result(self, num_relevant: int) -> dict[str, Any]:
        """Return zero result when no documents retrieved."""
        return {
            f"retrieval_precision@{self.k}": 0.0,
            f"retrieval_recall@{self.k}": 0.0,
            f"retrieval_f1@{self.k}": 0.0,
            "retrieval_mrr": 0.0,
            f"retrieval_ndcg@{self.k}": 0.0,
            "num_relevant_retrieved": 0,
            "num_retrieved": 0,
            "num_relevant_total": num_relevant,
        }
