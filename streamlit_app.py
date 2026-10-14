"""
DocuMind AI — Enterprise Intelligence Edition
Main Application Entry Point & Navigation Router
"From Documents to Decisions."
"""
import streamlit as st

# Configure Streamlit page layout
st.set_page_config(
    page_title="DocuMind AI — Enterprise Intelligence",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

from config import (
    APP_NAME, APP_SUBTITLE, APP_TAGLINE, VERSION,
    DEFAULT_VECTOR_STORE, DEFAULT_EMBEDDING_MODEL, PALETTE
)
from design_system import inject_custom_css
from core.database import init_db, get_all_chunks
from core.embeddings import get_embedding_engine
from core.vector_store import get_vector_store
from core.hybrid_retriever import HybridRetriever
from core.llm_provider import get_llm_provider
from core.rag_engine import RAGEngine

# Navigation Sections Mapping
NAV_SECTIONS = [
    ("Command Center", "🧭"),
    ("AI Research Workspace", "💬"),
    ("Knowledge Library", "📚"),
    ("Knowledge Graph Explorer", "🕸️"),
    ("Evidence and Contradiction Lab", "⚖️"),
    ("Document Intelligence Studio", "🔬"),
    ("Agent Control Room", "🤖"),
    ("RAG Evaluation Lab", "📊"),
    ("Prompt Engineering Studio", "🖋️"),
    ("Conversation History", "📜"),
    ("Data Sources and Ingestion", "📥"),
    ("Security and Governance", "🛡️"),
    ("Settings and Model Configuration", "⚙️")
]

def init_app_state():
    """Initializes and caches stateful singletons."""
    if "dark_mode" not in st.session_state:
        st.session_state["dark_mode"] = False

    if "nav_section" not in st.session_state:
        st.session_state["nav_section"] = "Command Center"

    if "vector_backend" not in st.session_state:
        st.session_state["vector_backend"] = DEFAULT_VECTOR_STORE

    if "embedding_model_name" not in st.session_state:
        st.session_state["embedding_model_name"] = DEFAULT_EMBEDDING_MODEL

    if "llm_provider_name" not in st.session_state:
        st.session_state["llm_provider_name"] = "Extractive Local (API-Free)"

    # Initialize Engine Components
    if "app_state" not in st.session_state:
        init_db()
        embed_eng = get_embedding_engine(st.session_state["embedding_model_name"])
        v_store = get_vector_store(st.session_state["vector_backend"])
        retriever = HybridRetriever(vector_store=v_store, embedding_engine=embed_eng)

        # Sync BM25 corpus on initial load
        all_chunks = get_all_chunks()
        retriever.sync_bm25_corpus(all_chunks)

        llm = get_llm_provider("extractive")
        rag = RAGEngine(retriever=retriever, llm_provider=llm)

        st.session_state["app_state"] = {
            "embedding_engine": embed_eng,
            "vector_store": v_store,
            "hybrid_retriever": retriever,
            "llm_provider": llm,
            "rag_engine": rag,
            "vector_backend": st.session_state["vector_backend"],
            "embedding_model_name": st.session_state["embedding_model_name"],
            "llm_provider_name": st.session_state["llm_provider_name"]
        }


def render_sidebar():
    """Renders the minimal editorial sidebar."""
    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 0.5rem 0 1rem 0;">
            <div style="font-size: 1.45rem; font-weight: 700; letter-spacing: -0.03em; color: {PALETTE['obsidian']};">
                {APP_NAME}
            </div>
            <div style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.12em; color: {PALETTE['cool_concrete']}; font-weight: 600; margin-top: 2px;">
                {APP_SUBTITLE}
            </div>
            <div style="font-size: 0.82rem; color: {PALETTE['shadowed_ash']}; font-style: italic; margin-top: 6px;">
                "{APP_TAGLINE}"
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<hr class="minimal-hr" style="margin: 0.8rem 0;">', unsafe_allow_html=True)

        # Navigation Menu
        current_nav = st.session_state["nav_section"]
        for section_name, icon in NAV_SECTIONS:
            is_active = (section_name == current_nav)
            btn_label = f"{icon}  {section_name}"
            # Render active state with custom visual indication
            if st.button(btn_label, key=f"nav_{section_name}", use_container_width=True):
                st.session_state["nav_section"] = section_name
                st.rerun()

        st.markdown('<hr class="minimal-hr" style="margin: 1.2rem 0;">', unsafe_allow_html=True)

        # Footer info
        st.markdown(f"""
        <div style="font-size: 0.74rem; color: {PALETTE['cool_concrete']}; line-height: 1.6;">
            <div>Engine: <b>v{VERSION}</b></div>
            <div>Theme: <b>Eliza Minimal</b></div>
            <div>Vector: <b>{st.session_state.get('vector_backend', 'FAISS').upper()}</b></div>
            <div>Mode: <b>Offline Ready</b></div>
        </div>
        """, unsafe_allow_html=True)


def main():
    init_app_state()
    inject_custom_css(dark_mode=st.session_state.get("dark_mode", False))
    render_sidebar()

    current_section = st.session_state["nav_section"]
    state = st.session_state["app_state"]

    # Route to designated section
    if current_section == "Command Center":
        from pages_ui import p01_command_center
        p01_command_center.render(state)
    elif current_section == "AI Research Workspace":
        from pages_ui import p02_research_workspace
        p02_research_workspace.render(state)
    elif current_section == "Knowledge Library":
        from pages_ui import p03_knowledge_library
        p03_knowledge_library.render(state)
    elif current_section == "Knowledge Graph Explorer":
        from pages_ui import p04_knowledge_graph
        p04_knowledge_graph.render(state)
    elif current_section == "Evidence and Contradiction Lab":
        from pages_ui import p05_evidence_lab
        p05_evidence_lab.render(state)
    elif current_section == "Document Intelligence Studio":
        from pages_ui import p06_doc_studio
        p06_doc_studio.render(state)
    elif current_section == "Agent Control Room":
        from pages_ui import p07_agent_control
        p07_agent_control.render(state)
    elif current_section == "RAG Evaluation Lab":
        from pages_ui import p08_rag_evaluation
        p08_rag_evaluation.render(state)
    elif current_section == "Prompt Engineering Studio":
        from pages_ui import p09_prompt_studio
        p09_prompt_studio.render(state)
    elif current_section == "Conversation History":
        from pages_ui import p10_conversation_history
        p10_conversation_history.render(state)
    elif current_section == "Data Sources and Ingestion":
        from pages_ui import p11_data_ingestion
        p11_data_ingestion.render(state)
    elif current_section == "Security and Governance":
        from pages_ui import p12_security_governance
        p12_security_governance.render(state)
    elif current_section == "Settings and Model Configuration":
        from pages_ui import p13_settings_observability
        p13_settings_observability.render(state)
    else:
        st.error(f"Unknown navigation section: {current_section}")

if __name__ == "__main__":
    main()
