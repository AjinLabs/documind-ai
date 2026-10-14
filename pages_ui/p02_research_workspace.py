"""
DocuMind AI — Page 2: AI Research Workspace
Grounded multi-turn conversational intelligence with verifiable citation chips,
source preview drawer, multilingual responses, and style controls.
"""
import uuid
import streamlit as st
from design_system import render_header, render_card
from core.database import (
    get_all_documents, get_collections, get_connection
)
from core.rag_engine import RAGEngine
from core.security import sanitize_user_input
from config import PALETTE

def render(state: dict):
    render_header(
        title="AI Research Workspace",
        subtitle="Verifiable conversational intelligence grounded in your indexed documents.",
        badge="Citation-First"
    )

    rag_engine: RAGEngine = state["rag_engine"]
    collections = ["All"] + get_collections()
    all_docs = get_all_documents()

    # Session ID management
    if "current_session_id" not in st.session_state:
        st.session_state["current_session_id"] = f"session_{uuid.uuid4().hex[:8]}"

    session_id = st.session_state["current_session_id"]

    # Top Controls Bar: Scope, Style, Language
    c1, c2, c3, c4 = st.columns([1.2, 1.0, 1.0, 0.8])
    with c1:
        selected_collection = st.selectbox("Knowledge Collection", collections, index=0)
    with c2:
        answer_style = st.selectbox("Answer Style", ["Detailed", "Concise", "Executive Brief"], index=0)
    with c3:
        language = st.selectbox("Language", ["English", "Malayalam", "Manglish"], index=0)
    with c4:
        if st.button("New Session", use_container_width=True):
            st.session_state["current_session_id"] = f"session_{uuid.uuid4().hex[:8]}"
            st.rerun()

    # Optional Document Scope Filter
    doc_options = {d["document_id"]: f"{d['filename']} ({d['page_count']} pages)" for d in all_docs}
    selected_doc_ids = st.multiselect(
        "Filter Specific Documents (leave empty to search entire selected collection)",
        options=list(doc_options.keys()),
        format_func=lambda x: doc_options.get(x, x)
    )

    st.markdown('<hr class="minimal-hr">', unsafe_allow_html=True)

    # Load message history for session from SQLite
    with get_connection() as conn:
        db_messages = conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,)
        ).fetchall()

    # Suggested Prompts if session is empty
    if not db_messages:
        st.markdown(f"<div style='font-size: 0.85rem; color: {PALETTE['shadowed_ash']}; margin-bottom: 8px;'>Suggested Inquiries:</div>", unsafe_allow_html=True)
        col_s1, col_s2, col_s3 = st.columns(3)
        sample_q1 = "Summarize the primary conclusions and strategic objectives."
        sample_q2 = "What are the key obligations, deadlines, and numerical figures?"
        sample_q3 = "Identify any conflicting assertions, ambiguities, or risks."

        prompt_to_run = None
        with col_s1:
            if st.button(sample_q1, key="sq1"):
                prompt_to_run = sample_q1
        with col_s2:
            if st.button(sample_q2, key="sq2"):
                prompt_to_run = sample_q2
        with col_s3:
            if st.button(sample_q3, key="sq3"):
                prompt_to_run = sample_q3
    else:
        prompt_to_run = None

    # Display Chat History
    for msg in db_messages:
        role = msg["role"]
        content = msg["content"]
        with st.chat_message(role):
            st.markdown(content)

    # Chat Input
    user_input = st.chat_input("Ask a question regarding your documents...") or prompt_to_run

    if user_input:
        # 1. Security Sanitization
        clean_input, is_safe, flag_msg = sanitize_user_input(user_input)

        # Show user message
        with st.chat_message("user"):
            st.markdown(clean_input)

        # Persist user message to SQLite
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO conversations (session_id, title, collection_name) VALUES (?, ?, ?) ON CONFLICT (session_id) DO UPDATE SET updated_at = CURRENT_TIMESTAMP",
                (session_id, clean_input[:40], selected_collection)
            )
            conn.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, 'user', ?)",
                (session_id, clean_input)
            )
            conn.commit()

        # Build chat history for conversational rewriting
        history_tuples = [{"role": m["role"], "content": m["content"]} for m in db_messages]

        # 2. Execute RAG
        with st.chat_message("assistant"):
            with st.spinner("Synthesizing grounded response with citations..."):
                rag_result = rag_engine.answer_query(
                    query=clean_input,
                    chat_history=history_tuples,
                    document_filter=selected_doc_ids if selected_doc_ids else None,
                    collection_filter=selected_collection,
                    answer_style=answer_style,
                    language=language
                )

                answer_text = rag_result["answer"]
                citations = rag_result["citations"]
                coverage = rag_result["coverage_rate"]
                latency = rag_result["latency_sec"]

                st.markdown(answer_text)

                # Citation Verification Chips
                if citations:
                    st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)
                    chip_htmls = []
                    for c in citations:
                        cls = "citation-chip citation-chip-verified" if c.get("is_verified") else "citation-chip"
                        icon = "✓" if c.get("is_verified") else "•"
                        chip_htmls.append(f'<span class="{cls}">{icon} {c.get("document")} (p. {c.get("page")})</span>')

                    st.markdown(f"""
                    <div style="font-size: 0.78rem; margin-top: 8px;">
                        <span style="color: {PALETTE['shadowed_ash']}; font-weight: 600; margin-right: 8px;">Verified Citations ({int(coverage*100)}% coverage):</span>
                        {' '.join(chip_htmls)}
                    </div>
                    """, unsafe_allow_html=True)

                # Expandable Source Passages Drawer
                if rag_result.get("retrieved_chunks"):
                    with st.expander(f"Inspect Retrieved Source Passages ({len(rag_result['retrieved_chunks'])} chunks | {latency}s)"):
                        for i, chunk in enumerate(rag_result["retrieved_chunks"]):
                            st.markdown(f"**Chunk {i+1} — {chunk.get('filename')} (Page {chunk.get('page_number')})**")
                            st.markdown(f"> \"{chunk.get('text_content')}\"")
                            st.caption(f"Relevance Score: {chunk.get('retrieval_score', 'N/A')} | Token Count: {chunk.get('token_count')}")

        # Persist assistant message to SQLite
        import json
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content, citations_json, model_used) VALUES (?, 'assistant', ?, ?, ?)",
                (session_id, answer_text, json.dumps(citations), state.get("llm_provider_name", "Extractive Local"))
            )
            conn.commit()
