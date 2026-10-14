"""
DocuMind AI — Chunking Engine
Splits page-extracted text into semantic, overlapping chunks while strictly
preserving document_id, page_number, and chunk_index provenance.
"""
import re
import uuid
from typing import List, Dict, Any
from config import DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP

def approximate_token_count(text: str) -> int:
    """Estimates tokens based on word and punctuation frequency (~1.3 tokens per word)."""
    words = re.findall(r"\w+|[^\w\s]", text, re.UNICODE)
    return max(1, int(len(words) * 1.15))


def chunk_document_pages(
    pages: List[Dict[str, Any]],
    document_id: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
) -> List[Dict[str, Any]]:
    """
    Chunks a list of pages. Each page produces chunks that preserve the page number.
    Uses sentence boundary splitting within each page.
    """
    all_chunks: List[Dict[str, Any]] = []
    global_chunk_index = 0

    # Clean sentence splitter regex
    sentence_splitter = re.compile(r"(?<=[.!?])\s+")

    for page in pages:
        page_num = page["page_number"]
        page_text = page["text"].strip()
        if not page_text:
            continue

        sentences = sentence_splitter.split(page_text)
        current_chunk_sentences: List[str] = []
        current_chunk_len = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sent_len = len(sentence)

            # If a single sentence is larger than chunk_size, split by character window
            if sent_len > chunk_size:
                # Flush existing buffer first
                if current_chunk_sentences:
                    chunk_text = " ".join(current_chunk_sentences)
                    all_chunks.append({
                        "chunk_id": f"{document_id}_p{page_num}_c{global_chunk_index}",
                        "document_id": document_id,
                        "chunk_index": global_chunk_index,
                        "page_number": page_num,
                        "text_content": chunk_text,
                        "token_count": approximate_token_count(chunk_text),
                        "embedding_model": embedding_model,
                        "metadata_json": "{}"
                    })
                    global_chunk_index += 1
                    current_chunk_sentences = []
                    current_chunk_len = 0

                # Slice large sentence
                start = 0
                while start < sent_len:
                    end = min(start + chunk_size, sent_len)
                    part = sentence[start:end].strip()
                    if part:
                        all_chunks.append({
                            "chunk_id": f"{document_id}_p{page_num}_c{global_chunk_index}",
                            "document_id": document_id,
                            "chunk_index": global_chunk_index,
                            "page_number": page_num,
                            "text_content": part,
                            "token_count": approximate_token_count(part),
                            "embedding_model": embedding_model,
                            "metadata_json": "{}"
                        })
                        global_chunk_index += 1
                    start += (chunk_size - chunk_overlap)
                continue

            if current_chunk_len + sent_len + 1 > chunk_size and current_chunk_sentences:
                # Emit current chunk
                chunk_text = " ".join(current_chunk_sentences)
                all_chunks.append({
                    "chunk_id": f"{document_id}_p{page_num}_c{global_chunk_index}",
                    "document_id": document_id,
                    "chunk_index": global_chunk_index,
                    "page_number": page_num,
                    "text_content": chunk_text,
                    "token_count": approximate_token_count(chunk_text),
                    "embedding_model": embedding_model,
                    "metadata_json": "{}"
                })
                global_chunk_index += 1

                # Keep overlap sentences
                overlap_sentences: List[str] = []
                overlap_len = 0
                for s in reversed(current_chunk_sentences):
                    if overlap_len + len(s) + 1 <= chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_len += len(s) + 1
                    else:
                        break
                current_chunk_sentences = overlap_sentences
                current_chunk_len = sum(len(s) + 1 for s in current_chunk_sentences)

            current_chunk_sentences.append(sentence)
            current_chunk_len += sent_len + 1

        # Flush any remaining text on the page
        if current_chunk_sentences:
            chunk_text = " ".join(current_chunk_sentences)
            all_chunks.append({
                "chunk_id": f"{document_id}_p{page_num}_c{global_chunk_index}",
                "document_id": document_id,
                "chunk_index": global_chunk_index,
                "page_number": page_num,
                "text_content": chunk_text,
                "token_count": approximate_token_count(chunk_text),
                "embedding_model": embedding_model,
                "metadata_json": "{}"
            })
            global_chunk_index += 1

    return all_chunks
