"""
DocuMind AI — Page 8: RAG Evaluation Lab
Deterministic evaluation suite: Precision@k, Recall@k, MRR, Citation Validity, and Groundedness.
"""
import json
import streamlit as st
from design_system import render_header, render_metric, render_card
from core.evaluation import RAGEvaluationHarness, STARTER_EVAL_BENCHMARK
from core.database import get_connection
from config import PALETTE

def render(state: dict):
    render_header(
        title="RAG Evaluation Lab",
        subtitle="Benchmark retrieval accuracy, groundedness, citation validity, and response latency.",
        badge="Evaluation Harness"
    )

    eval_harness = RAGEvaluationHarness(rag_engine=state["rag_engine"])

    col_btn1, col_btn2 = st.columns([1.5, 1])
    with col_btn1:
        exp_name = st.text_input("Experiment Name", value="Baseline Hybrid RAG Evaluation")
    with col_btn2:
        top_k_eval = st.slider("Top-K Evaluation Depth", min_value=1, max_value=8, value=3)

    if st.button("Run Benchmark Evaluation", type="primary"):
        with st.spinner("Executing benchmark evaluation suite across test cases..."):
            suite_summary = eval_harness.run_benchmark_suite(
                experiment_name=exp_name,
                benchmark_cases=STARTER_EVAL_BENCHMARK,
                retrieval_strategy=f"{state.get('vector_backend', 'FAISS').upper()} + BM25 RRF Fusion",
                embedding_model=state.get("embedding_model_name", "all-MiniLM-L6-v2")
            )
            st.session_state["latest_eval_summary"] = suite_summary
            st.success("Benchmark completed and recorded.")

    # Show Latest Results
    if "latest_eval_summary" in st.session_state:
        summary = st.session_state["latest_eval_summary"]

        st.markdown('<hr class="minimal-hr">', unsafe_allow_html=True)
        st.markdown(f"#### Experiment Results: `{summary['experiment_name']}`")

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.markdown(render_metric("Precision@K", f"{int(summary['avg_precision']*100)}%", f"k={top_k_eval}"), unsafe_allow_html=True)
        with c2:
            st.markdown(render_metric("Recall@K", f"{int(summary['avg_recall']*100)}%", "Ground truth match"), unsafe_allow_html=True)
        with c3:
            st.markdown(render_metric("MRR", f"{summary['avg_mrr']}", "Mean Reciprocal Rank"), unsafe_allow_html=True)
        with c4:
            st.markdown(render_metric("Groundedness", f"{int(summary['avg_groundedness']*100)}%", "Lexical support"), unsafe_allow_html=True)
        with c5:
            st.markdown(render_metric("Avg Latency", f"{summary['avg_latency_ms']} ms", "Pipeline turnaround"), unsafe_allow_html=True)

        st.markdown("##### Detailed Test Case Breakdown:")
        for tc in summary["details"]:
            tc_html = f"""
            <div style="font-weight: 600; font-size: 0.92rem; color: {PALETTE['obsidian']};">
                Test [{tc['test_id']}]: {tc['question']}
            </div>
            <div style="font-size: 0.8rem; color: {PALETTE['shadowed_ash']}; margin-top: 4px;">
                P@K: <b>{int(tc['precision_at_k']*100)}%</b> • Recall: <b>{int(tc['recall_at_k']*100)}%</b> • MRR: <b>{tc['mrr']}</b> • Groundedness: <b>{int(tc['groundedness']*100)}%</b> • Latency: <b>{tc['latency_ms']}ms</b>
            </div>
            """
            render_card(tc_html)

    # Historical Experiments Table
    st.markdown('<hr class="minimal-hr">', unsafe_allow_html=True)
    st.markdown("#### Historical Experiments")
    with get_connection() as conn:
        records = conn.execute("SELECT * FROM evaluation_records ORDER BY created_at DESC LIMIT 5").fetchall()

    if not records:
        st.caption("No historical records found.")
    else:
        for r in records:
            m = json.loads(r["metrics_json"])
            st.markdown(f"- **{r['experiment_name']}** ({r['created_at']}) — Avg P@K: `{m.get('avg_precision')}` | MRR: `{m.get('avg_mrr')}` | Strategy: `{r['retrieval_strategy']}`")
