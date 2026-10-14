"""
DocuMind AI — Page 13: Settings and System Observability
Runtime configuration, vector engine toggle, LLM credentials, and system observability diagnostics.
"""
import os
import shutil
import streamlit as st
from design_system import render_header, render_metric, render_card
from core.database import get_all_documents, get_all_chunks, get_connection
from core.security import redact_secrets
from config import (
    SQLITE_DB_PATH, UPLOADS_DIR, FAISS_DIR, CHROMA_DIR,
    DEFAULT_EMBEDDING_MODEL, PALETTE
)

def render(state: dict):
    render_header(
        title="Settings & System Observability",
        subtitle="Manage LLM providers, switch vector engines, and inspect system telemetry.",
        badge="System Health"
    )

    docs = get_all_documents()
    chunks = get_all_chunks()
    vector_store = state["vector_store"]

    # Calculate local storage usage
    db_size_mb = round(SQLITE_DB_PATH.stat().st_size / (1024 * 1024), 2) if SQLITE_DB_PATH.exists() else 0.0
    uploads_size_mb = round(sum(f.stat().st_size for f in UPLOADS_DIR.glob("*") if f.is_file()) / (1024 * 1024), 2)

    # 1. System Health & Observability Metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(render_metric("SQLite Database", "Connected", f"Size: {db_size_mb} MB (WAL)"), unsafe_allow_html=True)
    with c2:
        st.markdown(render_metric("Vector Engine", state.get("vector_backend", "FAISS").upper(), f"{vector_store.count()} indexed vectors"), unsafe_allow_html=True)
    with c3:
        st.markdown(render_metric("Upload Storage", f"{uploads_size_mb} MB", f"{len(docs)} PDF files stored"), unsafe_allow_html=True)
    with c4:
        st.markdown(render_metric("Embedding Space", "384-dim", state.get("embedding_model_name", "MiniLM")), unsafe_allow_html=True)

    st.markdown('<hr class="minimal-hr">', unsafe_allow_html=True)

    # 2. Runtime Model Configuration
    st.markdown("#### Model Providers & Offline Fallback Configuration")

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        provider_options = ["Extractive Local (API-Free)", "OpenAI (GPT-4o-mini)", "Google Gemini (2.5 Flash)", "Ollama (Local)"]
        current_provider = state.get("llm_provider_name", "Extractive Local (API-Free)")
        current_idx = provider_options.index(current_provider) if current_provider in provider_options else 0

        selected_provider = st.selectbox("LLM Provider", provider_options, index=current_idx)

        api_key_input = ""
        if "OpenAI" in selected_provider:
            api_key_input = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
        elif "Gemini" in selected_provider:
            api_key_input = st.text_input("Google Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""))
        elif "Ollama" in selected_provider:
            ollama_url = st.text_input("Ollama Host URL", value="http://localhost:11434")

    with col_m2:
        vector_backend_options = ["FAISS", "ChromaDB"]
        current_vb = state.get("vector_backend", "FAISS").upper()
        vb_idx = 0 if current_vb == "FAISS" else 1

        selected_vb = st.selectbox("Vector Store Backend", vector_backend_options, index=vb_idx)
        st.caption("FAISS provides ultra-fast in-memory/flat-file cosine search. ChromaDB provides persistent collection-oriented storage.")

        dark_mode_toggle = st.checkbox("Enable Dark Minimalist Theme", value=st.session_state.get("dark_mode", False))
        if dark_mode_toggle != st.session_state.get("dark_mode", False):
            st.session_state["dark_mode"] = dark_mode_toggle
            st.rerun()

    if st.button("Apply & Save Settings", type="primary"):
        st.session_state["llm_provider_name"] = selected_provider
        st.session_state["vector_backend"] = selected_vb.lower()

        if "OpenAI" in selected_provider and api_key_input:
            os.environ["OPENAI_API_KEY"] = api_key_input
        elif "Gemini" in selected_provider and api_key_input:
            os.environ["GEMINI_API_KEY"] = api_key_input

        # Update provider in state
        from core.llm_provider import get_llm_provider
        from core.vector_store import get_vector_store
        from core.rag_engine import RAGEngine

        ptype = "extractive"
        if "OpenAI" in selected_provider:
            ptype = "openai"
        elif "Gemini" in selected_provider:
            ptype = "gemini"
        elif "Ollama" in selected_provider:
            ptype = "ollama"

        new_llm = get_llm_provider(ptype, api_key=api_key_input)
        new_vs = get_vector_store(selected_vb.lower())

        state["llm_provider"] = new_llm
        state["llm_provider_name"] = selected_provider
        state["vector_store"] = new_vs
        state["vector_backend"] = selected_vb.lower()
        state["rag_engine"] = RAGEngine(state["hybrid_retriever"], new_llm)

        st.success("Settings applied successfully.")
        st.rerun()

    st.markdown('<hr class="minimal-hr">', unsafe_allow_html=True)

    # 3. Safe Purge & Maintenance
    with st.expander("Dangerous Operations: Purge All Knowledge"):
        st.warning("This operation will remove all indexed PDFs, SQLite chunks, and reset vector indexes.")
        if st.button("Purge All Data and Reset Index", key="btn_purge"):
            with get_connection() as conn:
                conn.execute("DELETE FROM documents")
                conn.execute("DELETE FROM chunks")
                conn.execute("DELETE FROM claims")
                conn.execute("DELETE FROM entities")
                conn.execute("DELETE FROM relationships")
                conn.execute("DELETE FROM conversations")
                conn.execute("DELETE FROM messages")
                conn.commit()
            vector_store.clear()
            st.success("All data purged and indexes reset.")
            st.rerun()
