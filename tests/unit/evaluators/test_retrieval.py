"""Unit tests for RAG retrieval evaluator.

Tests verify precision@k, recall@k, MRR, and NDCG calculations with various scenarios.
"""

import pytest

from medeval.evaluators.retrieval import RetrievalEvaluator
from medeval.models import ClinicalCase, Prediction, RetrievedDocument


def test_retrieval_perfect_ranking():
    """All relevant docs retrieved in perfect order at top."""
    case = ClinicalCase(
        id="test1",
        text="",
        symptoms=[],
        medications=[],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
        relevant_doc_ids=["doc1", "doc2", "doc3"],
    )

    prediction = Prediction(
        case_id="test1",
        summary_text="",
        medications=[],
        retrieved_docs=[
            RetrievedDocument(doc_id="doc1", text="", score=0.9, rank=1),
            RetrievedDocument(doc_id="doc2", text="", score=0.8, rank=2),
            RetrievedDocument(doc_id="doc3", text="", score=0.7, rank=3),
        ],
    )

    evaluator = RetrievalEvaluator(k=5)
    result = evaluator.evaluate(case, prediction)

    assert result["retrieval_precision@5"] == 1.0  # All retrieved are relevant
    assert result["retrieval_recall@5"] == 1.0  # All relevant retrieved
    assert result["retrieval_f1@5"] == 1.0
    assert result["retrieval_mrr"] == 1.0  # First doc is relevant
    assert result["retrieval_ndcg@5"] == 1.0  # Perfect ranking


def test_retrieval_partial_recall():
    """Some relevant docs retrieved, some missed."""
    case = ClinicalCase(
        id="test2",
        text="",
        symptoms=[],
        medications=[],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
        relevant_doc_ids=["doc1", "doc3", "doc5"],  # 3 relevant
    )

    prediction = Prediction(
        case_id="test2",
        summary_text="",
        medications=[],
        retrieved_docs=[
            RetrievedDocument(doc_id="doc1", text="", score=0.9, rank=1),
            RetrievedDocument(doc_id="doc2", text="", score=0.8, rank=2),  # Not relevant
            RetrievedDocument(doc_id="doc3", text="", score=0.7, rank=3),
            RetrievedDocument(doc_id="doc4", text="", score=0.6, rank=4),  # Not relevant
            RetrievedDocument(doc_id="doc6", text="", score=0.5, rank=5),  # Not relevant
        ],
    )

    evaluator = RetrievalEvaluator(k=5)
    result = evaluator.evaluate(case, prediction)

    assert result["retrieval_precision@5"] == 0.4  # 2/5 retrieved are relevant
    assert result["retrieval_recall@5"] == pytest.approx(0.667, abs=0.01)  # 2/3 relevant found
    assert result["retrieval_mrr"] == 1.0  # First doc is relevant
    assert result["num_relevant_retrieved"] == 2
    assert result["num_retrieved"] == 5
    assert result["num_relevant_total"] == 3


def test_retrieval_no_relevant_at_top():
    """First relevant doc appears late in ranking."""
    case = ClinicalCase(
        id="test3",
        text="",
        symptoms=[],
        medications=[],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
        relevant_doc_ids=["doc5"],
    )

    prediction = Prediction(
        case_id="test3",
        summary_text="",
        medications=[],
        retrieved_docs=[
            RetrievedDocument(doc_id="doc1", text="", score=0.9, rank=1),
            RetrievedDocument(doc_id="doc2", text="", score=0.8, rank=2),
            RetrievedDocument(doc_id="doc3", text="", score=0.7, rank=3),
            RetrievedDocument(doc_id="doc5", text="", score=0.6, rank=4),  # Relevant at rank 4
        ],
    )

    evaluator = RetrievalEvaluator(k=5)
    result = evaluator.evaluate(case, prediction)

    assert result["retrieval_mrr"] == 0.25  # 1/4 (first relevant at rank 4)
    assert result["retrieval_recall@5"] == 1.0  # Found the only relevant doc


def test_retrieval_no_docs_retrieved():
    """Edge case: No documents retrieved."""
    case = ClinicalCase(
        id="test4",
        text="",
        symptoms=[],
        medications=[],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
        relevant_doc_ids=["doc1", "doc2"],
    )

    prediction = Prediction(case_id="test4", summary_text="", medications=[], retrieved_docs=[])

    evaluator = RetrievalEvaluator(k=5)
    result = evaluator.evaluate(case, prediction)

    assert result["retrieval_precision@5"] == 0.0
    assert result["retrieval_recall@5"] == 0.0
    assert result["retrieval_mrr"] == 0.0
    assert result["retrieval_ndcg@5"] == 0.0


def test_retrieval_no_relevant_docs_in_ground_truth():
    """Edge case: No relevant docs defined (returns empty result)."""
    case = ClinicalCase(
        id="test5",
        text="",
        symptoms=[],
        medications=[],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
        relevant_doc_ids=None,
    )

    prediction = Prediction(
        case_id="test5",
        summary_text="",
        medications=[],
        retrieved_docs=[
            RetrievedDocument(doc_id="doc1", text="", score=0.9, rank=1),
        ],
    )

    evaluator = RetrievalEvaluator(k=5)
    result = evaluator.evaluate(case, prediction)

    # Should return None for metrics when no ground truth
    assert result["retrieval_precision@5"] is None
    assert result["retrieval_recall@5"] is None


def test_retrieval_k_parameter():
    """Test that k parameter limits evaluated documents."""
    case = ClinicalCase(
        id="test6",
        text="",
        symptoms=[],
        medications=[],
        required_facts=[],
        forbidden_facts=[],
        gold_summary={},
        relevant_doc_ids=["doc1", "doc10"],
    )

    prediction = Prediction(
        case_id="test6",
        summary_text="",
        medications=[],
        retrieved_docs=[
            RetrievedDocument(doc_id="doc1", text="", score=0.9, rank=1),
            RetrievedDocument(doc_id="doc2", text="", score=0.8, rank=2),
            RetrievedDocument(doc_id="doc3", text="", score=0.7, rank=3),
            RetrievedDocument(doc_id="doc10", text="", score=0.5, rank=10),  # Beyond k=3
        ],
    )

    # Evaluate with k=3 (should not see doc10)
    evaluator = RetrievalEvaluator(k=3)
    result = evaluator.evaluate(case, prediction)

    assert result["retrieval_recall@3"] == 0.5  # Only found 1 of 2 relevant docs
    assert result["num_relevant_retrieved"] == 1
    assert result["num_retrieved"] == 3  # Only top 3 considered
