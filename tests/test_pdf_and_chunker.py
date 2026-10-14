"""
Unit Tests for PDF Processor and Chunking Engine
"""
import pytest
from core.pdf_processor import calculate_content_hash, validate_pdf_bytes, normalize_text
from core.chunker import chunk_document_pages, approximate_token_count

def test_calculate_content_hash():
    data1 = b"%PDF-1.4 sample content for documind"
    data2 = b"%PDF-1.4 sample content for documind"
    data3 = b"%PDF-1.4 different content"
    assert calculate_content_hash(data1) == calculate_content_hash(data2)
    assert calculate_content_hash(data1) != calculate_content_hash(data3)

def test_validate_pdf_bytes():
    valid_pdf = b"%PDF-1.5 test document"
    is_valid, msg = validate_pdf_bytes(valid_pdf)
    assert is_valid is True

    empty_bytes = b""
    is_valid, msg = validate_pdf_bytes(empty_bytes)
    assert is_valid is False
    assert "empty" in msg.lower()

    corrupt_bytes = b"NOT_A_PDF_FILE"
    is_valid, msg = validate_pdf_bytes(corrupt_bytes)
    assert is_valid is False
    assert "invalid pdf" in msg.lower()

def test_normalize_text():
    raw = "Hello   world!\x00This is\u00a0a\n\n\n\ntest."
    clean = normalize_text(raw)
    assert "\x00" not in clean
    assert "\u00a0" not in clean
    assert "\n\n\n\n" not in clean
    assert "Hello world!" in clean

def test_chunk_document_pages_provenance():
    pages = [
        {"page_number": 1, "text": "Sentence one on page one. Sentence two on page one with more details."},
        {"page_number": 2, "text": "Page two discusses financial projections and deliverables."}
    ]
    chunks = chunk_document_pages(pages, document_id="doc_test_123", chunk_size=100, chunk_overlap=20)
    assert len(chunks) >= 2
    # Check page preservation
    assert chunks[0]["page_number"] == 1
    assert chunks[0]["document_id"] == "doc_test_123"
    assert "p1" in chunks[0]["chunk_id"]

    page_2_chunks = [c for c in chunks if c["page_number"] == 2]
    assert len(page_2_chunks) >= 1
    assert "financial projections" in page_2_chunks[0]["text_content"]

def test_approximate_token_count():
    text = "DocuMind transforms unstructured PDFs into decisions."
    count = approximate_token_count(text)
    assert count >= 6
