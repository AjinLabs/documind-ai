"""
DocuMind AI — Page 10: Conversation History
Multi-session persistent chat manager, conversation search, session resume, and markdown export.
"""
import streamlit as st
from design_system import render_header, render_card
from core.database import get_connection
from config import PALETTE

def render(state: dict):
    render_header(
        title="Conversation History",
        subtitle="Review, resume, search, and export multi-turn research conversations.",
        badge="Session History"
    )

    search_term = st.text_input("Search Past Research Conversations", placeholder="Search by topic or session title...")

    with get_connection() as conn:
        if search_term.strip():
            sessions = conn.execute("""
            SELECT c.*, COUNT(m.id) as msg_count
            FROM conversations c
            LEFT JOIN messages m ON c.session_id = m.session_id
            WHERE c.title LIKE ? OR c.session_id LIKE ?
            GROUP BY c.session_id
            ORDER BY c.updated_at DESC
            """, (f"%{search_term}%", f"%{search_term}%")).fetchall()
        else:
            sessions = conn.execute("""
            SELECT c.*, COUNT(m.id) as msg_count
            FROM conversations c
            LEFT JOIN messages m ON c.session_id = m.session_id
            GROUP BY c.session_id
            ORDER BY c.updated_at DESC
            """).fetchall()

    if not sessions:
        st.info("No saved research conversations found.")
        return

    st.markdown(f"**Found {len(sessions)} research sessions:**")

    for s in sessions:
        sid = s["session_id"]
        title = s["title"]
        updated = s["updated_at"]
        count = s["msg_count"]
        collection = s["collection_name"]

        card_html = f"""
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <div style="font-weight: 600; font-size: 1.05rem; color: {PALETTE['obsidian']};">{title}</div>
                <div style="font-size: 0.8rem; color: {PALETTE['shadowed_ash']}; margin-top: 4px;">
                    Session: <code>{sid}</code> • Messages: <b>{count}</b> • Collection: <b>{collection}</b>
                </div>
            </div>
            <div style="font-size: 0.75rem; color: {PALETTE['cool_concrete']};">
                Updated: {updated}
            </div>
        </div>
        """
        render_card(card_html)

        b1, b2, b3 = st.columns([1, 1, 2])
        with b1:
            if st.button("Resume Chat", key=f"resume_{sid}"):
                st.session_state["current_session_id"] = sid
                st.session_state["nav_section"] = "AI Research Workspace"
                st.rerun()
        with b2:
            if st.button("Delete", key=f"del_sess_{sid}"):
                with get_connection() as conn:
                    conn.execute("DELETE FROM conversations WHERE session_id = ?", (sid,))
                    conn.execute("DELETE FROM messages WHERE session_id = ?", (sid,))
                    conn.commit()
                st.success("Session deleted.")
                st.rerun()
        with b3:
            # Export conversation as Markdown
            with get_connection() as conn:
                m_rows = conn.execute("SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC", (sid,)).fetchall()
            chat_md = f"# DocuMind Research Session: {title}\nSession ID: {sid}\n\n---\n\n"
            for m in m_rows:
                chat_md += f"### {m['role'].upper()} ({m['created_at']}):\n{m['content']}\n\n"

            st.download_button(
                "Export (.md)",
                data=chat_md,
                file_name=f"{sid}.md",
                mime="text/markdown",
                key=f"export_{sid}"
            )
