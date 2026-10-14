"""
DocuMind AI — Page 7: Agent Control Room
Bounded Agentic Research Orchestrator with execution logs, research plans, tool calls, and report synthesis.
"""
import streamlit as st
from design_system import render_header, render_metric, render_card
from core.agent_orchestrator import ResearchOrchestrator
from core.database import get_collections, get_connection
from core.intelligence_studio import IntelligenceStudioEngine
from config import PALETTE

def render(state: dict):
    render_header(
        title="Agent Control Room",
        subtitle="Bounded multi-step autonomous research orchestrator with deterministic safety limits.",
        badge="Bounded Agent"
    )

    orchestrator = ResearchOrchestrator(
        retriever=state["hybrid_retriever"],
        llm_provider=state["llm_provider"]
    )
    studio = IntelligenceStudioEngine(llm_provider=state["llm_provider"])
    collections = ["All"] + get_collections()

    c1, c2 = st.columns([2, 1])
    with c1:
        research_goal = st.text_input(
            "Research Objective / Complex Inquiry",
            placeholder="e.g. Compare the financial projections, obligations, and risk factors across all indexed reports."
        )
    with c2:
        selected_collection = st.selectbox("Target Collection Scope", collections, index=0)

    # Configuration limits
    with st.expander("Agent Safety & Iteration Controls"):
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            max_iter = st.slider("Maximum Iterations", min_value=1, max_value=8, value=4)
        with col_l2:
            max_tools = st.slider("Maximum Tool Calls", min_value=2, max_value=15, value=8)

    if st.button("Launch Bounded Research Agent", type="primary"):
        if not research_goal.strip():
            st.warning("Please specify a research objective.")
        else:
            with st.spinner("Executing bounded research state machine..."):
                task_result = orchestrator.execute_research(
                    research_goal=research_goal.strip(),
                    collection_name=selected_collection,
                    max_iterations=max_iter,
                    max_tool_calls=max_tools
                )
                st.session_state["latest_agent_result"] = task_result
                st.success(f"Research finalized in {task_result['execution_time_sec']}s ({task_result['tool_calls_used']} tool calls).")

    # Render Task Results
    if "latest_agent_result" in st.session_state:
        res = st.session_state["latest_agent_result"]

        st.markdown('<hr class="minimal-hr">', unsafe_allow_html=True)
        st.markdown(f"### Research Task: `{res['task_id']}`")

        # Metrics
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(render_metric("Execution Duration", f"{res['execution_time_sec']}s", "Bounded execution"), unsafe_allow_html=True)
        with m2:
            st.markdown(render_metric("Tool Calls", f"{res['tool_calls_used']}", "Sandboxed queries"), unsafe_allow_html=True)
        with m3:
            st.markdown(render_metric("Evidence Chunks", f"{len(res['evidence'])}", "Verified excerpts"), unsafe_allow_html=True)

        tab_report, tab_plan, tab_logs = st.tabs(["Synthesized Report", "Execution Plan", "Audit Logs"])

        with tab_report:
            st.markdown(res["report_markdown"])
            r_col1, r_col2 = st.columns(2)
            with r_col1:
                st.download_button(
                    "Download Intelligence Report (.md)",
                    data=res["report_markdown"],
                    file_name=f"{res['task_id']}_report.md",
                    mime="text/markdown"
                )
            with r_col2:
                try:
                    pdf_bytes = studio.export_report_to_pdf(f"DocuMind Research Brief: {res['task_id']}", res["report_markdown"])
                    st.download_button(
                        "Export Formal PDF (.pdf)",
                        data=pdf_bytes,
                        file_name=f"{res['task_id']}_report.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.caption(f"PDF export notice: {e}")

        with tab_plan:
            st.markdown("#### Autonomous Research Decomposition:")
            for p in res["plan"]:
                st.markdown(f"- {p}")

        with tab_logs:
            st.markdown("#### Transparent Tool Execution Log:")
            for log in res["logs"]:
                st.markdown(f"**[{log['timestamp']}s] {log['step']}** ➔ `{log['action']}`")
                st.caption(log['summary'])
