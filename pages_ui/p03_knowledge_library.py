"""
DocuMind AI — Page 3: Knowledge Library
Document collections manager, metadata inspection, chunk explorer, and safe deletion.
"""
import streamlit as st
from design_system import render_header, render_card
from core.database import (
    get_all_documents, get_collections, add_collection,
    get_chunks_for_document, delete_document
)
from core.vector_store import VectorStoreInterface
from config import PALETTE

def render(state: dict):
    render_header(
        title="Knowledge Library",
        subtitle="Manage indexed document collections, provenance metadata, and vector storage.",
        badge="Library"
    )

    vector_store: VectorStoreInterface = state["vector_store"]
    collections = ["All"] + get_collections()

    top_c1, top_c2 = st.columns([2, 1])
    with top_c1:
        selected_col = st.selectbox("Filter Collection", collections, index=0)
    with top_c2:
        with st.expander("Create New Collection"):
            new_col_name = st.text_input("Collection Name", placeholder="e.g. Legal, Finance, Q3 Reports")
            new_col_desc = st.text_input("Description", placeholder="Brief description")
            if st.button("Save Collection", key="btn_add_col"):
                if new_col_name.strip():
                    add_collection(new_col_name.strip(), new_col_desc.strip())
                    st.success(f"Collection '{new_col_name}' created.")
                    st.rerun()

    docs = get_all_documents(collection=selected_col)

    if not docs:
        st.info("No documents found in this collection. Upload PDFs from 'Data Sources and Ingestion' to build your knowledge base.")
        if st.button("Go to Document Ingestion"):
            st.session_state["nav_section"] = "Data Sources and Ingestion"
            st.rerun()
        return

    st.markdown(f"**Found {len(docs)} documents** in collection `{selected_col}`:")

    for doc in docs:
        doc_id = doc["document_id"]
        fname = doc["filename"]
        pages = doc["page_count"]
        size_kb = round(doc["file_size_bytes"] / 1024, 1)
        created = doc["created_at"]
        hash_short = doc["content_hash"][:12]
        col_name = doc["collection_name"]
        is_scanned = doc.get("is_scanned", 0)

        card_html = f"""
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <div style="font-weight: 600; font-size: 1.05rem; color: {PALETTE['obsidian']};">{fname}</div>
                <div style="font-size: 0.8rem; color: {PALETTE['shadowed_ash']}; margin-top: 4px;">
                    Collection: <b>{col_name}</b> • Pages: <b>{pages}</b> • Size: <b>{size_kb} KB</b> • Hash: <code>{hash_short}</code>
                    {f'<span class="status-pill status-review" style="margin-left: 8px;">Scanned/OCR</span>' if is_scanned else ''}
                </div>
            </div>
            <div style="font-size: 0.75rem; color: {PALETTE['cool_concrete']};">
                Indexed: {created}
            </div>
        </div>
        """
        render_card(card_html)

        # Action buttons per document
        b_col1, b_col2, b_col3 = st.columns([1, 1, 3])
        with b_col1:
            if st.button(f"View Chunks", key=f"view_{doc_id}"):
                st.session_state[f"show_chunks_{doc_id}"] = not st.session_state.get(f"show_chunks_{doc_id}", False)
        with b_col2:
            if st.button(f"Delete", key=f"del_{doc_id}"):
                delete_document(doc_id)
                vector_store.delete_document(doc_id)
                st.success(f"Deleted '{fname}' and invalidated associated vectors.")
                st.rerun()

        if st.session_state.get(f"show_chunks_{doc_id}", False):
            chunks = get_chunks_for_document(doc_id)
            st.markdown(f"**Text Chunks ({len(chunks)}) for `{fname}`:**")
            for c in chunks[:8]:
                st.markdown(f"- **Chunk {c['chunk_index']} (Page {c['page_number']})** [{c['token_count']} tokens]:")
                st.text(c['text_content'][:240] + "...")
            if len(chunks) > 8:
                st.caption(f"...and {len(chunks)-8} more chunks.")
