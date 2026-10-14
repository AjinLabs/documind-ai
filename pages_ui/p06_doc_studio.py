"""
DocuMind AI — Page 6: Document Intelligence Studio
14 high-precision document analysis tools with Pydantic validation,
structured extraction, and PDF / Markdown export.
"""
import streamlit as st
from design_system import render_header, render_card
from core.database import get_all_documents, get_chunks_for_document
from core.intelligence_studio import IntelligenceStudioEngine
from core.version_intelligence import VersionIntelligenceEngine
from config import PALETTE

TOOLS = [
    "Executive Brief",
    "Document Summary",
    "Chapter & Section Summary",
    "Technical Explanation",
    "Key Concepts & Glossary",
    "Timeline Extraction",
    "Action-Item Extraction",
    "Structured JSON Extraction (Pydantic)",
    "Question Generation",
    "Study Notes",
    "Meeting / Report Briefing",
    "Decision-Support Report",
    "Document Version Diff",
    "Table Extractor"
]

def render(state: dict):
    render_header(
        title="Document Intelligence Studio",
        subtitle="Extract structured intelligence, executive briefs, action items, and audit-ready reports.",
        badge="14 Tools"
    )

    studio_engine = IntelligenceStudioEngine(llm_provider=state["llm_provider"])
    version_engine = VersionIntelligenceEngine()
    all_docs = get_all_documents()

    if not all_docs:
        st.info("No documents indexed yet. Ingest documents to unlock Document Intelligence Studio tools.")
        return

    doc_map = {d["document_id"]: d["filename"] for d in all_docs}

    c1, c2 = st.columns([1.2, 1.2])
    with c1:
        selected_tool = st.selectbox("Select Intelligence Tool", TOOLS, index=0)
    with c2:
        selected_doc_id = st.selectbox(
            "Target Document",
            options=list(doc_map.keys()),
            format_func=lambda x: doc_map[x]
        )

    # For Document Version Diff tool, allow picking a second document
    secondary_doc_id = None
    if selected_tool == "Document Version Diff":
        secondary_doc_id = st.selectbox(
            "Comparison / Revision Document",
            options=[k for k in doc_map.keys() if k != selected_doc_id] or list(doc_map.keys()),
            format_func=lambda x: doc_map[x]
        )

    st.markdown('<hr class="minimal-hr">', unsafe_allow_html=True)

    if st.button(f"Execute {selected_tool}", type="primary"):
        with st.spinner(f"Running {selected_tool}..."):
            doc_chunks = get_chunks_for_document(selected_doc_id)

            if selected_tool == "Structured JSON Extraction (Pydantic)":
                result_json = studio_engine.extract_structured_json(doc_chunks)
                st.session_state["studio_output_type"] = "json"
                st.session_state["studio_output"] = result_json
            elif selected_tool == "Document Version Diff" and secondary_doc_id:
                doc_b_chunks = get_chunks_for_document(secondary_doc_id)
                diff_res = version_engine.compare_documents(
                    doc_chunks,
                    doc_b_chunks,
                    doc_map[selected_doc_id],
                    doc_map[secondary_doc_id]
                )
                st.session_state["studio_output_type"] = "diff"
                st.session_state["studio_output"] = diff_res
            else:
                result_text = studio_engine.run_tool(selected_tool, doc_chunks)
                st.session_state["studio_output_type"] = "text"
                st.session_state["studio_output"] = result_text

    # Render Output if available
    if "studio_output" in st.session_state:
        out_type = st.session_state.get("studio_output_type", "text")
        output = st.session_state["studio_output"]

        st.markdown(f"#### Generated Intelligence: {selected_tool}")

        if out_type == "json":
            st.json(output)
            json_str = json.dumps(output, indent=2)
            st.download_button(
                "Export Structured JSON",
                data=json_str,
                file_name=f"documind_extracted_{selected_doc_id[:8]}.json",
                mime="application/json"
            )
        elif out_type == "diff":
            st.markdown(f"**Similarity Score:** `{output['similarity_percentage']}%`")
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                st.metric("Additions", output["additions_count"])
            with col_d2:
                st.metric("Deletions", output["deletions_count"])
            with col_d3:
                st.metric("Clause Shifts", output["changed_figures_count"])

            if output["changed_figures"]:
                st.markdown("##### Detected Shifted Numbers / Values:")
                for cf in output["changed_figures"]:
                    st.markdown(f"- Previous: `\"{cf['previous_clause']}\"` ➔ Updated: `\"{cf['updated_clause']}\"`")

            with st.expander("Inspect Raw Unified Diff Output"):
                st.code(output["diff_text"], language="diff")

        else:
            st.markdown(output)

            # Export Buttons: Markdown & PDF
            col_e1, col_e2 = st.columns([1, 1])
            with col_e1:
                st.download_button(
                    "Download Markdown (.md)",
                    data=output,
                    file_name=f"{selected_tool.replace(' ', '_').lower()}.md",
                    mime="text/markdown"
                )
            with col_e2:
                try:
                    pdf_bytes = studio_engine.export_report_to_pdf(f"DocuMind Studio: {selected_tool}", output)
                    st.download_button(
                        "Export Formal PDF (.pdf)",
                        data=pdf_bytes,
                        file_name=f"{selected_tool.replace(' ', '_').lower()}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.caption(f"PDF export notice: {e}")
