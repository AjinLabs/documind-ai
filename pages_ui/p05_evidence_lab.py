"""
DocuMind AI — Page 5: Evidence and Contradiction Lab
Cross-document claim analysis, side-by-side contradiction detection, and reviewer ledger.
"""
import streamlit as st
from design_system import render_header, render_metric, render_card
from core.database import get_all_chunks
from core.evidence_engine import EvidenceEngine
from config import PALETTE

def render(state: dict):
    render_header(
        title="Evidence & Contradiction Lab",
        subtitle="Detect conflicting statements, extract key assertions, and audit documentary evidence.",
        badge="Verification Lab"
    )

    evidence_engine = EvidenceEngine()

    c1, c2 = st.columns([2, 1])
    with c1:
        status_filter = st.selectbox(
            "Filter Claim Status",
            ["All", "supported", "potentially_contradicted", "requires_human_review", "insufficient_evidence"],
            index=0
        )
    with c2:
        if st.button("Run Claim & Contradiction Scan", use_container_width=True):
            with st.spinner("Extracting factual claims and scanning cross-document contradictions..."):
                all_chunks = get_all_chunks()
                raw_claims = evidence_engine.extract_claims_from_chunks(all_chunks)
                analyzed = evidence_engine.detect_cross_contradictions(raw_claims)
                evidence_engine.save_claims(analyzed)
                st.success(f"Extracted and cross-examined {len(analyzed)} assertions.")
                st.rerun()

    claims = evidence_engine.get_all_claims(status_filter=status_filter)

    # Metrics
    total = len(claims)
    contradicted = sum(1 for c in claims if c["verification_status"] == "potentially_contradicted")
    supported = sum(1 for c in claims if c["verification_status"] == "supported")

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(render_metric("Total Claims", str(total), "Extracted atomic assertions"), unsafe_allow_html=True)
    with m2:
        st.markdown(render_metric("Contradiction Flags", str(contradicted), "Requiring cross-examination"), unsafe_allow_html=True)
    with m3:
        st.markdown(render_metric("Verified Grounded", str(supported), "Supported by text"), unsafe_allow_html=True)

    st.markdown('<hr class="minimal-hr">', unsafe_allow_html=True)

    if not claims:
        st.info("No claims recorded yet. Click 'Run Claim & Contradiction Scan' to analyze all indexed documents.")
        return

    st.markdown(f"#### Active Claims Ledger ({len(claims)})")

    for claim in claims[:12]:
        cid = claim["claim_id"]
        ctext = claim["claim_text"]
        doc_name = claim.get("filename") or claim.get("document_id")
        page = claim["page_number"]
        status = claim["verification_status"]
        contradictions = claim.get("contradictions", [])
        reviewer_notes = claim.get("reviewer_notes", "")

        status_class = {
            "supported": "status-supported",
            "potentially_contradicted": "status-contradicted",
            "requires_human_review": "status-review",
            "insufficient_evidence": "status-insufficient"
        }.get(status, "status-review")

        card_html = f"""
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="font-weight: 600; font-size: 0.95rem; color: {PALETTE['obsidian']};">
                "{ctext}"
            </div>
            <span class="status-pill {status_class}">{status.replace('_', ' ').title()}</span>
        </div>
        <div style="font-size: 0.78rem; color: {PALETTE['shadowed_ash']}; margin-top: 6px;">
            Source: <b>{doc_name}</b> (Page {page}) • Claim ID: <code>{cid}</code>
        </div>
        """
        render_card(card_html)

        # Side-by-side contradiction panel if flagged
        if contradictions:
            st.warning("Potential Cross-Document Discrepancy Detected:")
            for contra in contradictions:
                st.markdown(f"""
                > **Opposing Passage in Document `{contra.get('document_id')}` (Page {contra.get('page_number')}):**  
                > \"{contra.get('passage')}\"  
                > *Reason: {contra.get('reason')}*
                """)

        # Reviewer Action Bar
        with st.expander(f"Review & Adjudicate Claim `{cid}`"):
            new_status = st.selectbox(
                "Update Verification Status",
                ["supported", "potentially_contradicted", "insufficient_evidence", "requires_human_review"],
                index=["supported", "potentially_contradicted", "insufficient_evidence", "requires_human_review"].index(status) if status in ["supported", "potentially_contradicted", "insufficient_evidence", "requires_human_review"] else 0,
                key=f"status_sel_{cid}"
            )
            notes = st.text_input("Reviewer Audit Notes", value=reviewer_notes, key=f"notes_{cid}")
            if st.button("Save Adjudication", key=f"save_rev_{cid}"):
                evidence_engine.update_reviewer_status(cid, new_status, notes)
                st.success("Reviewer ledger updated.")
                st.rerun()
