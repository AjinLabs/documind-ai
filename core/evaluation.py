"""
DocuMind AI — RAG Evaluation Harness
Computes deterministic retrieval and generation metrics:
Precision@k, Recall@k, Mean Reciprocal Rank (MRR), Citation Validity Rate,
Groundedness Estimate, and Execution Latency.
"""
import time
import json
import uuid
import logging
from typing import List, Dict, Any, Tuple
from core.database import get_connection

logger = logging.getLogger(__name__)

# Starter benchmark evaluation questions with ground truth
STARTER_EVAL_BENCHMARK = [
    {
        "id": "q1",
        "question": "What are the primary operational obligations and delivery milestones?",
        "expected_keywords": ["deliverable", "milestone", "shall", "obligations", "schedule"],
        "expected_documents": ["agreement.pdf", "report.pdf"],
        "expected_pages": [1, 2, 3]
    },
    {
        "id": "q2",
        "question": "What is the total reported financial revenue or budget allocation?",
        "expected_keywords": ["revenue", "budget", "total", "$", "allocation", "expenditure"],
        "expected_documents": ["financials.pdf", "annual_report.pdf"],
        "expected_pages": [1, 4]
    },
    {
        "id": "q3",
        "question": "Who is the designated executive officer or signatory on this matter?",
        "expected_keywords": ["officer", "signatory", "director", "dr.", "authorized", "ceo"],
        "expected_documents": ["policy.pdf", "contract.pdf"],
        "expected_pages": [1, 2]
    }
]

class RAGEvaluationHarness:
    def __init__(self, rag_engine):
        self.rag = rag_engine

    def evaluate_test_case(self, test_case: Dict[str, Any], top_k: int = 3) -> Dict[str, Any]:
        """Runs a single test case through the RAG pipeline and computes quality metrics."""
        start_time = time.time()
        question = test_case["question"]
        expected_docs = [d.lower() for d in test_case.get("expected_documents", [])]
        expected_pages = test_case.get("expected_pages", [])
        expected_keywords = [k.lower() for k in test_case.get("expected_keywords", [])]

        # Execute RAG query
        rag_output = self.rag.answer_query(query=question, top_k=top_k)
        retrieved = rag_output.get("retrieved_chunks", [])
        answer = rag_output.get("answer", "")
        citations = rag_output.get("citations", [])

        # 1. Precision@k: fraction of retrieved chunks matching expected documents or keywords
        relevant_retrieved = 0
        first_relevant_rank = None

        for rank, chunk in enumerate(retrieved):
            c_doc = (chunk.get("filename") or chunk.get("document_id", "")).lower()
            c_page = chunk.get("page_number", 0)
            c_text = chunk.get("text_content", "").lower()

            is_doc_match = any(ed in c_doc for ed in expected_docs)
            is_page_match = c_page in expected_pages
            is_keyword_match = any(kw in c_text for kw in expected_keywords)

            if is_doc_match or is_page_match or is_keyword_match:
                relevant_retrieved += 1
                if first_relevant_rank is None:
                    first_relevant_rank = rank + 1

        precision_at_k = round(relevant_retrieved / max(1, len(retrieved)), 2)

        # 2. Recall@k estimate
        recall_at_k = round(relevant_retrieved / max(1, len(expected_pages) or 1), 2)

        # 3. Mean Reciprocal Rank (MRR)
        mrr = round(1.0 / first_relevant_rank, 2) if first_relevant_rank else 0.0

        # 4. Citation Validity Rate
        citation_validity = rag_output.get("coverage_rate", 1.0)

        # 5. Groundedness Estimate (Lexical overlap between answer and retrieved chunks)
        combined_context = " ".join([c.get("text_content", "").lower() for c in retrieved])
        answer_words = set(answer.lower().split())
        overlap = sum(1 for w in answer_words if len(w) > 3 and w in combined_context)
        groundedness = round(min(1.0, overlap / max(1, len(answer_words) * 0.7)), 2)

        latency_ms = round((time.time() - start_time) * 1000, 1)

        return {
            "test_id": test_case.get("id"),
            "question": question,
            "precision_at_k": precision_at_k,
            "recall_at_k": recall_at_k,
            "mrr": mrr,
            "citation_validity": citation_validity,
            "groundedness": groundedness,
            "latency_ms": latency_ms,
            "retrieved_count": len(retrieved),
            "citations_found": len(citations)
        }

    def run_benchmark_suite(
        self,
        experiment_name: str = "Standard Baseline",
        benchmark_cases: Optional[List[Dict[str, Any]]] = None,
        retrieval_strategy: str = "Hybrid (Dense + BM25)",
        embedding_model: str = "all-MiniLM-L6-v2"
    ) -> Dict[str, Any]:
        """Runs the benchmark suite and records results in SQLite."""
        cases = benchmark_cases or STARTER_EVAL_BENCHMARK
        results = []

        for case in cases:
            res = self.evaluate_test_case(case)
            results.append(res)

        avg_precision = round(sum(r["precision_at_k"] for r in results) / max(1, len(results)), 2)
        avg_recall = round(sum(r["recall_at_k"] for r in results) / max(1, len(results)), 2)
        avg_mrr = round(sum(r["mrr"] for r in results) / max(1, len(results)), 2)
        avg_groundedness = round(sum(r["groundedness"] for r in results) / max(1, len(results)), 2)
        avg_latency = round(sum(r["latency_ms"] for r in results) / max(1, len(results)), 1)

        summary = {
            "eval_id": f"eval_{uuid.uuid4().hex[:8]}",
            "experiment_name": experiment_name,
            "cases_evaluated": len(results),
            "avg_precision": avg_precision,
            "avg_recall": avg_recall,
            "avg_mrr": avg_mrr,
            "avg_groundedness": avg_groundedness,
            "avg_latency_ms": avg_latency,
            "details": results
        }

        # Persist to SQLite
        with get_connection() as conn:
            conn.execute("""
            INSERT INTO evaluation_records (eval_id, experiment_name, dataset_name, retrieval_strategy, embedding_model, metrics_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                summary["eval_id"],
                experiment_name,
                "Starter Benchmark",
                retrieval_strategy,
                embedding_model,
                json.dumps(summary)
            ))
            conn.commit()

        return summary
