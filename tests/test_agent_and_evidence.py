"""
Unit Tests for Bounded Agentic Research Orchestrator and Evidence Engine
"""
import pytest
from core.agent_orchestrator import ResearchOrchestrator
from core.evidence_engine import EvidenceEngine
from core.hybrid_retriever import HybridRetriever
from core.llm_provider import ExtractiveLocalProvider
from core.vector_store import FAISSVectorStore
from core.embeddings import get_embedding_engine

@pytest.fixture
def agent_fixture(tmp_path):
    embed_engine = get_embedding_engine()
    vstore = FAISSVectorStore(index_dir=tmp_path, dim=embed_engine.dim)
    chunks = [
        {"chunk_id": "c1", "document_id": "report_2025.pdf", "filename": "report_2025.pdf", "page_number": 2, "text_content": "Company achieved 25% profit growth in Q3."},
        {"chunk_id": "c2", "document_id": "audit_2025.pdf", "filename": "audit_2025.pdf", "page_number": 5, "text_content": "Company suffered 10% operating loss in Q3 due to liabilities."}
    ]
    vectors = embed_engine.embed_texts([c["text_content"] for c in chunks])
    vstore.add_chunks(chunks, vectors)

    retriever = HybridRetriever(vstore, embed_engine)
    retriever.sync_bm25_corpus(chunks)
    llm = ExtractiveLocalProvider()
    return ResearchOrchestrator(retriever, llm), chunks

def test_bounded_agent_execution(agent_fixture):
    orchestrator, _ = agent_fixture
    result = orchestrator.execute_research(
        research_goal="Synthesize profit and loss findings",
        max_iterations=3,
        max_tool_calls=5
    )

    assert result["status"] == "completed"
    assert result["iterations_used"] <= 3
    assert result["tool_calls_used"] <= 5
    assert len(result["plan"]) > 0
    assert len(result["logs"]) > 0
    assert "report_markdown" in result
    assert "Executive Summary" in result["report_markdown"]

def test_evidence_contradiction_detection():
    engine = EvidenceEngine()
    chunks = [
        {"chunk_id": "c1", "document_id": "doc_a", "page_number": 1, "text_content": "Reported profit increased by 15% in Q4."},
        {"chunk_id": "c2", "document_id": "doc_b", "page_number": 2, "text_content": "Reported profit decreased by 5% in Q4."}
    ]

    claims = engine.extract_claims_from_chunks(chunks)
    assert len(claims) >= 2

    analyzed = engine.detect_cross_contradictions(claims)
    contradicted = [c for c in analyzed if c["verification_status"] == "potentially_contradicted"]
    assert len(contradicted) >= 1
    assert len(contradicted[0]["contradictions"]) >= 1
