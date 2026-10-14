"""
DocuMind AI — Page 9: Prompt Engineering Studio
Interactive prompt development, persona templates, context injection tuning, and test playground.
"""
import streamlit as st
from design_system import render_header, render_card
from core.security import redact_secrets
from config import PALETTE

TEMPLATES = {
    "Research Analyst": (
        "You are an elite Research Analyst at DocuMind AI. Provide thorough, objective analysis grounded "
        "strictly in the retrieved source passages. Cite every claim as [filename, p. X]. Never extrapolate beyond source bounds."
    ),
    "Executive Summarizer": (
        "You are an Executive Intelligence Officer. Synthesize high-level strategic takeaways, quantitative benchmarks, "
        "and critical risks into an executive format with inline citations."
    ),
    "Evidence Verifier": (
        "You are a Forensic Evidence Verifier. Scrutinize the documentary text for factual consistency, conflicting dates, "
        "unsupported assertions, and ambiguities. Cite every source explicitly."
    ),
    "Technical Assistant": (
        "You are a Senior Technical Systems Specialist. Explain architectural structures, protocols, and technical procedures "
        "with maximum clarity and precision."
    ),
    "Study Assistant": (
        "You are an academic mentor. Synthesize document concepts into structured Cornell study notes, highlighting core definitions "
        "and self-examination questions."
    )
}

def render(state: dict):
    render_header(
        title="Prompt Engineering Studio",
        subtitle="Fine-tune persona instructions, citation policies, and test system prompts live.",
        badge="Prompt Studio"
    )

    rag_engine = state["rag_engine"]

    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown("#### Persona Presets")
        selected_preset = st.radio("Choose Persona", list(TEMPLATES.keys()), index=0)

        tone = st.selectbox("Tone", ["Analytical & Formal", "Direct & Concise", "Academic", "Executive"], index=0)
        citation_rule = st.selectbox("Citation Strictness", ["Strict (Mandatory [filename, p. X])", "Standard", "Relaxed"], index=0)

    with c2:
        st.markdown("#### Active System Prompt")
        default_prompt = TEMPLATES[selected_preset]
        active_prompt = st.text_area(
            "System Prompt Template",
            value=default_prompt,
            height=160
        )

        st.caption("Secrets in prompt templates are automatically sanitized before evaluation.")

    st.markdown('<hr class="minimal-hr">', unsafe_allow_html=True)

    # Live Test Playground
    st.markdown("#### Live Prompt Playground")
    test_q = st.text_input("Test Question", value="What are the primary conclusions and risks identified?")

    if st.button("Run Test with Custom Prompt", type="primary"):
        with st.spinner("Executing RAG with customized prompt parameters..."):
            res = rag_engine.answer_query(
                query=test_q,
                custom_system_prompt=redact_secrets(active_prompt)
            )
            st.markdown("##### Assistant Response:")
            st.markdown(res["answer"])
            if res.get("citations"):
                st.caption(f"Citation Coverage: {int(res['coverage_rate']*100)}% | Turnaround: {res['latency_sec']}s")
