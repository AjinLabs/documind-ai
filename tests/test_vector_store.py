"""
Unit Tests for Vector Store Backends (FAISS and ChromaDB)
"""
import pytest
import numpy as np
from core.vector_store import FAISSVectorStore, ChromaVectorStore
from core.embeddings import get_embedding_engine

def test_faiss_vector_store(tmp_path):
    embed_engine = get_embedding_engine()
    store = FAISSVectorStore(index_dir=tmp_path, dim=embed_engine.dim)

    chunks = [
        {"chunk_id": "c1", "document_id": "doc_a", "page_number": 1, "text_content": "Deep learning models for document analysis."},
        {"chunk_id": "c2", "document_id": "doc_b", "page_number": 2, "text_content": "Financial statement balance sheet and revenue."}
    ]
    texts = [c["text_content"] for c in chunks]
    vectors = embed_engine.embed_texts(texts)

    store.add_chunks(chunks, vectors)
    assert store.count() == 2

    # Search for deep learning
    q_vec = embed_engine.embed_query("machine learning AI models")
    results = store.search(q_vec, top_k=2)
    assert len(results) == 2
    assert results[0][0]["chunk_id"] == "c1"

    # Test filtering by document_id
    filtered = store.search(q_vec, top_k=2, document_filter=["doc_b"])
    assert len(filtered) == 1
    assert filtered[0][0]["document_id"] == "doc_b"

    # Test deletion
    store.delete_document("doc_a")
    assert store.count() == 1
    post_del = store.search(q_vec, top_k=2)
    assert len(post_del) == 1
    assert post_del[0][0]["document_id"] == "doc_b"

def test_chroma_vector_store(tmp_path):
    embed_engine = get_embedding_engine()
    store = ChromaVectorStore(persist_dir=tmp_path, collection_name="test_col")

    chunks = [
        {"chunk_id": "ch1", "document_id": "doc_x", "page_number": 1, "text_content": "Quarterly operating margins expanded significantly."}
    ]
    vectors = embed_engine.embed_texts([c["text_content"] for c in chunks])
    store.add_chunks(chunks, vectors)

    assert store.count() >= 1

    q_vec = embed_engine.embed_query("operating margins")
    hits = store.search(q_vec, top_k=1)
    assert len(hits) == 1
    assert hits[0][0]["document_id"] == "doc_x"

    store.delete_document("doc_x")
    assert store.count() == 0
