"""
DocuMind AI — Page 4: Knowledge Graph Explorer
Interactive visualization of entities and provenance-backed relationships across indexed documents.
"""
import streamlit as st
import streamlit.components.v1 as components
from design_system import render_header, render_metric, render_card
from core.database import get_all_documents, get_all_chunks
from core.knowledge_graph import KnowledgeGraphEngine
from config import PALETTE

def render(state: dict):
    render_header(
        title="Knowledge Graph Explorer",
        subtitle="Discover hidden relational networks, co-occurring entities, and cross-document links.",
        badge="Entity Intelligence"
    )

    kg_engine = KnowledgeGraphEngine()
    all_docs = get_all_documents()

    c1, c2 = st.columns([2, 1])
    with c1:
        doc_filter = st.selectbox(
            "Filter by Document Source",
            ["All"] + [d["filename"] for d in all_docs],
            index=0
        )
    with c2:
        if st.button("Extract / Refresh Graph Knowledge", use_container_width=True):
            with st.spinner("Extracting entities and relationships from indexed chunks..."):
                all_chunks = get_all_chunks()
                entities, relationships = kg_engine.extract_from_chunks(all_chunks)
                kg_engine.persist_graph(entities, relationships)
                st.success(f"Harvested {len(entities)} entities and {len(relationships)} relationships.")
                st.rerun()

    # Load graph data
    target_doc_id = None
    if doc_filter != "All":
        matched = [d["document_id"] for d in all_docs if d["filename"] == doc_filter]
        if matched:
            target_doc_id = matched[0]

    nodes, edges = kg_engine.get_graph_data(document_id=target_doc_id)

    # Metrics
    m1, m2 = st.columns(2)
    with m1:
        st.markdown(render_metric("Entities Extracted", str(len(nodes)), "Canonical entity nodes"), unsafe_allow_html=True)
    with m2:
        st.markdown(render_metric("Verified Relationships", str(len(edges)), "Provenance-linked relations"), unsafe_allow_html=True)

    st.markdown('<hr class="minimal-hr">', unsafe_allow_html=True)

    if not nodes:
        st.info("The knowledge graph is currently empty. Click 'Extract / Refresh Graph Knowledge' above to scan your indexed documents.")
        return

    # Render Interactive Graph
    st.markdown("#### Interactive Relational Graph")
    st.caption("Drag nodes, zoom in, or hover over edges to inspect source evidence passages.")
    graph_html = kg_engine.generate_html_graph(nodes, edges)
    components.html(graph_html, height=540, scrolling=False)

    # Provenance Table
    if edges:
        st.markdown("#### Provenance Evidence Ledger")
        for edge in edges[:8]:
            edge_html = f"""
            <div style="display: flex; justify-content: space-between; align-items: baseline;">
                <div>
                    <b>{edge['source_entity']}</b>
                    <span style="color: {PALETTE['cool_concrete']}; font-size: 0.8rem; margin: 0 6px;">──[{edge['relation_type']}]──►</span>
                    <b>{edge['target_entity']}</b>
                </div>
                <div style="font-size: 0.78rem; color: {PALETTE['shadowed_ash']};">
                    Page {edge['page_number']}
                </div>
            </div>
            <div style="font-size: 0.82rem; color: {PALETTE['shadowed_ash']}; margin-top: 6px; font-style: italic;">
                "{edge.get('evidence_text')}"
            </div>
            """
            render_card(edge_html)
