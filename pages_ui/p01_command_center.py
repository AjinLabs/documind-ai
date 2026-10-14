"""
DocuMind AI — Page 1: Command Center
Executive overview of indexed knowledge, real vector store metrics, system health, and recent intelligence tasks.
"""
import streamlit as st
from design_system import render_header, render_metric, render_card
from core.database import get_all_documents, get_collections, get_all_chunks, get_connection
from core.vector_store import get_vector_store
from config import APP_NAME, APP_TAGLINE, PALETTE

def render(state: dict):
    render_header(
        title="Command Center",
        subtitle=f"{APP_NAME} — {APP_TAGLINE} Architectural Knowledge Overview.",
        badge="Enterprise Live"
    )

    # 1. Fetch live metrics from SQLite & Vector Store
    docs = get_all_documents()
    collections = get_collections()
    chunks = get_all_chunks()
    vector_store = state.get("vector_store") or get_vector_store()
    vector_count = vector_store.count()

    with get_connection() as conn:
        claims_count = conn.execute("SELECT COUNT(*) as c FROM claims").fetchone()["c"]
        verified_claims = conn.execute("SELECT COUNT(*) as c FROM claims WHERE verification_status = 'supported'").fetchone()["c"]
        recent_tasks = conn.execute("SELECT * FROM research_tasks ORDER BY created_at DESC LIMIT 5").fetchall()

    # 2. Metric Grid
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(render_metric("Documents Indexed", str(len(docs)), f"{len(chunks)} text chunks"), unsafe_allow_html=True)
    with c2:
        st.markdown(render_metric("Knowledge Collections", str(len(collections)), "Separated namespaces"), unsafe_allow_html=True)
    with c3:
        st.markdown(render_metric("Vector Embeddings", str(vector_count), f"{state.get('vector_backend', 'FAISS').upper()} backend"), unsafe_allow_html=True)
    with c4:
        st.markdown(render_metric("Verified Evidence", f"{verified_claims}/{claims_count}", "Cross-document claims"), unsafe_allow_html=True)

    st.markdown('<hr class="minimal-hr">', unsafe_allow_html=True)

    # 3. Two-Column Dashboard: Quick Intelligence Actions + Recent Activity
    left_col, right_col = st.columns([1.1, 1.2])

    with left_col:
        st.markdown("#### Quick Intelligence Actions")
        st.markdown(
            "Access key intelligence pipelines directly or upload new documents to expand knowledge boundaries."
        )

        b1, b2 = st.columns(2)
        with b1:
            if st.button("AI Research Chat", use_container_width=True):
                st.session_state["nav_section"] = "AI Research Workspace"
                st.rerun()
            if st.button("Agent Control Room", use_container_width=True):
                st.session_state["nav_section"] = "Agent Control Room"
                st.rerun()
        with b2:
            if st.button("Ingest New Documents", use_container_width=True):
                st.session_state["nav_section"] = "Data Sources and Ingestion"
                st.rerun()
            if st.button("Explore Knowledge Graph", use_container_width=True):
                st.session_state["nav_section"] = "Knowledge Graph Explorer"
                st.rerun()

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # System Health Card
        health_html = f"""
        <div style="font-size: 0.88rem; line-height: 1.8;">
            <div style="font-weight: 600; margin-bottom: 6px; color: {PALETTE['obsidian']};">System Health Status</div>
            <div>• Database: <span style="color: {PALETTE['success']}; font-weight: 600;">Connected (SQLite WAL)</span></div>
            <div>• Vector Index: <span style="color: {PALETTE['success']}; font-weight: 600;">Online ({vector_count} vectors)</span></div>
            <div>• Active Provider: <span style="color: {PALETTE['charcoal_silk']}; font-weight: 600;">{state.get('llm_provider_name', 'Extractive Local (API-Free)')}</span></div>
            <div>• Embedding Engine: <span style="color: {PALETTE['charcoal_silk']}; font-weight: 600;">{state.get('embedding_model_name', 'all-MiniLM-L6-v2')}</span></div>
        </div>
        """
        render_card(health_html)

    with right_col:
        st.markdown("#### Recent Research Tasks")
        if not recent_tasks:
            st.info("No research tasks executed yet. Launch a research inquiry from the AI Research Workspace or Agent Control Room.")
        else:
            for task in recent_tasks:
                task_html = f"""
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 4px;">
                    <div style="font-weight: 600; font-size: 0.92rem; color: {PALETTE['obsidian']};">{task['query']}</div>
                    <span class="status-pill status-supported">Completed</span>
                </div>
                <div style="font-size: 0.78rem; color: {PALETTE['shadowed_ash']};">
                    Collection: <b>{task['collection_name']}</b> • Completed at {task['completed_at']}
                </div>
                """
                render_card(task_html)
