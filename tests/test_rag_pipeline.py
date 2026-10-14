"""
Unit Tests for RAG Pipeline, Query Rewriting, and Citation Validation
"""
import pytest
from core.rag_engine import RAGEngine
from core.hybrid_retriever import HybridRetriever
from core.llm_provider import ExtractiveLocalProvider
from core.vector_store import FAISSVectorStore
from core.embeddings import get_embedding_engine

@pytest.fixture
def test_rag(tmp_path):
    embed_engine = get_embedding_engine()
    vstore = FAISSVectorStore(index_dir=tmp_path, dim=embed_engine.dim)
    chunks = [
        {"chunk_id": "c1", "document_id": "report.pdf", "filename": "report.pdf", "page_number": 3, "text_content": "Projected revenue for FY2026 is $45 million."},
        {"chunk_id": "c2", "document_id": "policy.pdf", "filename": "policy.pdf", "page_number": 1, "text_content": "The compliance audit must be completed by November 15."}
    ]
    vectors = embed_engine.embed_texts([c["text_content"] for c in chunks])
    vstore.add_chunks(chunks, vectors)

    retriever = HybridRetriever(vstore, embed_engine)
    retriever.sync_bm25_corpus(chunks)
    llm = ExtractiveLocalProvider()
    return RAGEngine(retriever, llm)

def test_query_rewriting(test_rag):
    history = [
        {"role": "user", "content": "What is the projected revenue in FY2026?"},
        {"role": "assistant", "content": "Projected revenue is $45 million [report.pdf, p. 3]."}
    ]
    # Follow-up question with pronoun
    rewritten = test_rag.rewrite_query("what about it?", history)
    assert "projected revenue" in rewritten.lower()

def test_classify_intent(test_rag):
    assert test_rag.classify_intent("compare report A and report B") == "comparison"
    assert test_rag.classify_intent("summarize this section") == "summary"
    assert test_rag.classify_intent("when was the agreement signed?") == "fact_lookup"

def test_citation_validation(test_rag):
    retrieved = [
        {"filename": "report.pdf", "document_id": "report.pdf", "page_number": 3, "text_content": "Sample text"}
    ]
    answer_valid = "Revenue was $45M [report.pdf, p. 3]."
    cites, cov = test_rag.validate_citations(answer_valid, retrieved)
    assert len(cites) == 1
    assert cites[0]["is_verified"] is True
    assert cov == 1.0

    answer_invalid = "Random statement [unknown.pdf, p. 99]."
    cites_inv, cov_inv = test_rag.validate_citations(answer_invalid, retrieved)
    assert len(cites_inv) == 1
    assert cites_inv[0]["is_verified"] is False
    assert cov_inv == 0.0

def test_grounded_answer_generation(test_rag):
    output = test_rag.answer_query("What is the projected revenue?")
    assert "45 million" in output["answer"]
    assert output["latency_sec"] > 0
    assert len(output["retrieved_chunks"]) >= 1

def test_insufficient_evidence(test_rag):
    # Search for completely non-existent topic with low threshold
    output = test_rag.answer_query(
        "astrophysics galactic rotation curve of Andromeda galaxy",
        document_filter=["non_existent_doc_id"]
    )
    assert "insufficient evidence" in output["answer"].lower()
