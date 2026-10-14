"""
DocuMind AI — Page 11: Data Sources and Ingestion
Enterprise document ingestion engine: PDF validation, PyMuPDF extraction,
SHA-256 duplicate detection, configurable chunking, and batch vector indexing.
"""
import uuid
import time
import streamlit as st
from design_system import render_header, render_metric, render_card
from core.pdf_processor import extract_pdf_data, calculate_content_hash
from core.chunker import chunk_document_pages
from core.database import (
    get_document_by_hash, insert_document, insert_chunks,
    get_collections, get_all_chunks, log_audit_event
)
from core.security import sanitize_filename
from config import (
    DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP, MAX_UPLOAD_SIZE_MB,
    UPLOADS_DIR, PALETTE
)

def render(state: dict):
    render_header(
        title="Data Sources & Ingestion",
        subtitle="Ingest unstructured PDFs into verified, searchable knowledge with page-level provenance.",
        badge="Ingestion Pipeline"
    )

    vector_store = state["vector_store"]
    embedding_engine = state["embedding_engine"]
    collections = get_collections()

    # Upload & Chunking Configuration Controls
    with st.expander("Ingestion Pipeline Configuration", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            dest_collection = st.selectbox("Target Collection", collections, index=0)
        with c2:
            chunk_size = st.slider("Chunk Size (characters)", min_value=300, max_value=1600, value=DEFAULT_CHUNK_SIZE, step=50)
        with c3:
            chunk_overlap = st.slider("Chunk Overlap (characters)", min_value=30, max_value=350, value=DEFAULT_CHUNK_OVERLAP, step=10)

    # File Uploader
    uploaded_files = st.file_uploader(
        "Upload PDF Documents",
        type=["pdf"],
        accept_multiple_files=True,
        help=f"Maximum file size: {MAX_UPLOAD_SIZE_MB} MB per PDF"
    )

    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} file(s) selected for processing.**")

        if st.button("Start Batch Ingestion Pipeline", type="primary"):
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            processed_count = 0
            skipped_duplicates = 0

            for idx, uploaded_file in enumerate(uploaded_files):
                fname = sanitize_filename(uploaded_file.name)
                status_text.text(f"Processing ({idx+1}/{len(uploaded_files)}): {fname}...")
                file_bytes = uploaded_file.read()

                # 1. Duplicate Detection using SHA-256
                chash = calculate_content_hash(file_bytes)
                existing_doc = get_document_by_hash(chash)
                if existing_doc:
                    st.warning(f"Duplicate skipped: '{fname}' matches already indexed document '{existing_doc['filename']}'.")
                    skipped_duplicates += 1
                    continue

                try:
                    # 2. Extract PDF Data with PyMuPDF
                    pdf_data = extract_pdf_data(file_bytes, fname)
                    doc_id = f"doc_{uuid.uuid4().hex[:8]}"

                    # Save file locally
                    local_path = UPLOADS_DIR / f"{doc_id}_{fname}"
                    with open(local_path, "wb") as f:
                        f.write(file_bytes)

                    # 3. Insert Document record
                    insert_document({
                        "document_id": doc_id,
                        "filename": fname,
                        "content_hash": chash,
                        "collection_name": dest_collection,
                        "page_count": pdf_data["page_count"],
                        "file_size_bytes": pdf_data["file_size_bytes"],
                        "tags": "",
                        "is_scanned": 1 if pdf_data["is_scanned"] else 0,
                        "extraction_status": "indexed"
                    })

                    # 4. Chunk Pages
                    chunks = chunk_document_pages(
                        pages=pdf_data["pages"],
                        document_id=doc_id,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                        embedding_model=embedding_engine.model_name
                    )

                    # Augment chunk dictionaries with metadata
                    for c in chunks:
                        c["filename"] = fname
                        c["collection_name"] = dest_collection

                    # 5. Insert Chunks into SQLite
                    insert_chunks(chunks)

                    # 6. Generate Batch Embeddings & Index in Vector Store
                    if chunks:
                        texts_to_embed = [c["text_content"] for c in chunks]
                        embeddings = embedding_engine.embed_texts(texts_to_embed)
                        vector_store.add_chunks(chunks, embeddings)

                    # 7. Update Hybrid Retriever's BM25 Corpus
                    all_chunks = get_all_chunks()
                    state["hybrid_retriever"].sync_bm25_corpus(all_chunks)

                    log_audit_event("DOCUMENT_INGESTED", {
                        "document_id": doc_id,
                        "filename": fname,
                        "pages": pdf_data["page_count"],
                        "chunks": len(chunks)
                    })

                    processed_count += 1

                except Exception as e:
                    st.error(f"Error processing {fname}: {e}")
                    log_audit_event("INGESTION_ERROR", {"filename": fname, "error": str(e)}, severity="ERROR")

                progress_bar.progress((idx + 1) / len(uploaded_files))

            status_text.text("Ingestion batch completed.")
            st.success(f"Successfully processed {processed_count} document(s). ({skipped_duplicates} duplicate(s) omitted).")
            time.sleep(1)
            st.rerun()
