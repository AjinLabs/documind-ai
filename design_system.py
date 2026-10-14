"""
DocuMind AI — Design System & Custom Minimalist Styling
Implements the "Eliza" Minimalist Editorial Palette:
- Charcoal Silk: #3C4449
- Cool Concrete: #8D9295
- Shadowed Ash: #62676B
- Morning Mist: #CED3D6
- Obsidian: #151618
"""
import streamlit as st
from config import PALETTE

def inject_custom_css(dark_mode: bool = False):
    """Injects high-end, editorial, human-centered minimal CSS styling."""
    bg_color = PALETTE["bg_dark"] if dark_mode else PALETTE["bg_light"]
    card_bg = PALETTE["surface_dark"] if dark_mode else PALETTE["surface_light"]
    text_primary = "#F4F5F7" if dark_mode else PALETTE["obsidian"]
    text_secondary = PALETTE["morning_mist"] if dark_mode else PALETTE["shadowed_ash"]
    border_color = PALETTE["border_dark"] if dark_mode else PALETTE["border_light"]
    header_gradient = (
        "linear-gradient(180deg, #F4F5F7 0%, #CED3D6 100%)"
        if dark_mode
        else f"linear-gradient(180deg, {PALETTE['obsidian']} 0%, {PALETTE['charcoal_silk']} 100%)"
    )

    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: {text_primary};
        background-color: {bg_color};
    }}

    /* Main container spacing */
    .block-container {{
        padding-top: 1.8rem;
        padding-bottom: 3.5rem;
        padding-left: 2.2rem;
        padding-right: 2.2rem;
        max-width: 1380px;
    }}

    /* Subtle top bar */
    .stApp {{
        background-color: {bg_color};
    }}

    /* Editorial Typography */
    .editorial-title {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 700;
        font-size: 2.2rem;
        letter-spacing: -0.03em;
        line-height: 1.15;
        background: {header_gradient};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }}

    .editorial-serif {{
        font-family: 'Newsreader', serif;
        font-style: italic;
        font-weight: 400;
        font-size: 1.35rem;
        color: {text_secondary};
    }}

    .editorial-tagline {{
        font-size: 0.95rem;
        color: {text_secondary};
        font-weight: 400;
        letter-spacing: 0.01em;
        margin-bottom: 1.8rem;
    }}

    /* Minimalist Cards */
    .doc-card {{
        background-color: {card_bg};
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 1.4rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 2px 8px rgba(21, 22, 24, 0.03);
        transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
    }}
    .doc-card:hover {{
        border-color: {PALETTE["cool_concrete"]};
        box-shadow: 0 4px 14px rgba(21, 22, 24, 0.06);
    }}

    /* Metric Box */
    .metric-card {{
        background-color: {card_bg};
        border: 1px solid {border_color};
        border-radius: 10px;
        padding: 1.1rem 1.2rem;
        text-align: left;
    }}
    .metric-value {{
        font-size: 1.85rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        color: {text_primary};
        line-height: 1.1;
    }}
    .metric-label {{
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: {text_secondary};
        margin-top: 0.4rem;
        font-weight: 600;
    }}

    /* Citation Badges */
    .citation-chip {{
        display: inline-flex;
        align-items: center;
        background-color: {card_bg};
        border: 1px solid {PALETTE["morning_mist"]};
        color: {PALETTE["charcoal_silk"]};
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.78rem;
        font-family: 'JetBrains Mono', monospace;
        margin-right: 6px;
        margin-bottom: 4px;
    }}
    .citation-chip-verified {{
        background-color: rgba(45, 106, 79, 0.08);
        border: 1px solid rgba(45, 106, 79, 0.3);
        color: #1b4332;
    }}

    /* Status Pills */
    .status-pill {{
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.74rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }}
    .status-supported {{
        background-color: rgba(45, 106, 79, 0.12);
        color: {PALETTE["success"]};
        border: 1px solid rgba(45, 106, 79, 0.3);
    }}
    .status-contradicted {{
        background-color: rgba(176, 125, 30, 0.12);
        color: {PALETTE["warning"]};
        border: 1px solid rgba(176, 125, 30, 0.3);
    }}
    .status-insufficient {{
        background-color: rgba(158, 42, 43, 0.12);
        color: {PALETTE["danger"]};
        border: 1px solid rgba(158, 42, 43, 0.3);
    }}
    .status-review {{
        background-color: rgba(60, 68, 73, 0.1);
        color: {PALETTE["charcoal_silk"]};
        border: 1px solid {PALETTE["morning_mist"]};
    }}

    /* Minimalist Streamlit Overrides */
    div[data-testid="stSidebarNav"] {{
        display: none;
    }}
    section[data-testid="stSidebar"] {{
        background-color: {card_bg};
        border-right: 1px solid {border_color};
    }}
    .stButton>button {{
        border-radius: 8px;
        background-color: {PALETTE["obsidian"]};
        color: #FFFFFF !important;
        border: 1px solid {PALETTE["charcoal_silk"]};
        font-weight: 500;
        font-size: 0.88rem;
        padding: 0.45rem 1.1rem;
        transition: all 0.15s ease;
    }}
    .stButton>button:hover {{
        background-color: {PALETTE["charcoal_silk"]};
        border-color: {PALETTE["cool_concrete"]};
        color: #FFFFFF !important;
    }}

    /* Secondary button styling */
    .secondary-btn>button {{
        background-color: transparent !important;
        color: {text_primary} !important;
        border: 1px solid {border_color} !important;
    }}
    .secondary-btn>button:hover {{
        background-color: {card_bg} !important;
        border-color: {PALETTE["cool_concrete"]} !important;
    }}

    /* Clean divider */
    .minimal-hr {{
        border: 0;
        height: 1px;
        background-color: {border_color};
        margin: 1.5rem 0;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_header(title: str, subtitle: str = "", badge: str = ""):
    """Renders a minimalist, architectural header."""
    badge_html = f'<span class="status-pill status-review" style="vertical-align: middle; margin-left: 10px;">{badge}</span>' if badge else ""
    st.markdown(f"""
    <div style="margin-bottom: 1.4rem;">
        <div class="editorial-title" style="display: flex; align-items: center; justify-content: space-between;">
            <div>{title} {badge_html}</div>
        </div>
        {f'<div class="editorial-tagline">{subtitle}</div>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)


def render_card(content_html: str):
    """Wraps HTML content in a minimalist card."""
    st.markdown(f'<div class="doc-card">{content_html}</div>', unsafe_allow_html=True)


def render_metric(label: str, value: str, subtext: str = ""):
    """Renders a single metric box."""
    subtext_html = f'<div style="font-size: 0.72rem; color: #8D9295; margin-top: 4px;">{subtext}</div>' if subtext else ""
    return f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        {subtext_html}
    </div>
    """
