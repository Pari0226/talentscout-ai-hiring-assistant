"""
TalentScout Hiring Assistant
Main Streamlit application entry point.
"""

from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass  # fall back to shell exports

import streamlit as st
from src.ui import render_ui

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TalentScout | Hiring Assistant",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&display=swap');

/* ── Root tokens ── */
:root {
    --bg:        #0d0f14;
    --surface:   #161920;
    --surface2:  #1e2230;
    --border:    #2a2f3d;
    --accent:    #00e5a0;
    --accent2:   #0090ff;
    --danger:    #ff5c5c;
    --text:      #e8eaf0;
    --muted:     #7a7f96;
    --radius:    14px;
}

/* ── Global reset ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem !important; max-width: 760px !important; }

/* ── App header ── */
.ts-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 24px 28px;
    background: linear-gradient(135deg, #161d2e 0%, #0d141f 100%);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}
.ts-header::before {
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 160px; height: 160px;
    background: radial-gradient(circle, rgba(0,229,160,.15) 0%, transparent 70%);
    pointer-events: none;
}
.ts-logo {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 1.6rem;
    color: var(--accent);
    letter-spacing: -0.5px;
    line-height: 1;
}
.ts-tagline {
    font-size: 0.78rem;
    color: var(--muted);
    margin-top: 3px;
    letter-spacing: 0.4px;
    text-transform: uppercase;
}
.ts-badge {
    margin-left: auto;
    background: rgba(0,229,160,.12);
    border: 1px solid rgba(0,229,160,.3);
    color: var(--accent);
    font-size: 0.7rem;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 20px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

/* ── Progress tracker ── */
.ts-progress {
    display: flex;
    gap: 6px;
    margin-bottom: 20px;
    align-items: center;
}
.ts-step {
    flex: 1;
    height: 4px;
    border-radius: 2px;
    background: var(--border);
    transition: background .4s ease;
}
.ts-step.done   { background: var(--accent); }
.ts-step.active { background: linear-gradient(90deg, var(--accent), var(--accent2)); }
.ts-step-label {
    font-size: 0.7rem;
    color: var(--muted);
    white-space: nowrap;
    margin-left: 8px;
}

/* ── Chat bubbles ── */
.ts-chat-wrap {
    display: flex;
    flex-direction: column;
    gap: 14px;
    margin-bottom: 20px;
    max-height: 520px;
    overflow-y: auto;
    padding-right: 4px;
}
.ts-bubble {
    display: flex;
    gap: 10px;
    align-items: flex-start;
}
.ts-bubble.user { flex-direction: row-reverse; }

.ts-avatar {
    width: 34px; height: 34px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.9rem;
    flex-shrink: 0;
    font-weight: 700;
}
.ts-avatar.bot  { background: linear-gradient(135deg,#00e5a0,#0090ff); color:#0d0f14; }
.ts-avatar.user { background: var(--surface2); color: var(--muted); border: 1px solid var(--border); }

.ts-msg {
    max-width: 78%;
    padding: 12px 16px;
    border-radius: var(--radius);
    font-size: 0.88rem;
    line-height: 1.6;
}
.ts-msg.bot {
    background: var(--surface);
    border: 1px solid var(--border);
    border-top-left-radius: 4px;
}
.ts-msg.user {
    background: linear-gradient(135deg, rgba(0,144,255,.18), rgba(0,229,160,.12));
    border: 1px solid rgba(0,229,160,.2);
    border-top-right-radius: 4px;
    text-align: right;
}

/* ── Input area ── */
.stTextInput > div > div > input {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 12px 16px !important;
    transition: border-color .2s;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(0,229,160,.1) !important;
}
.stTextInput > div > div > input::placeholder { color: var(--muted) !important; }

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, var(--accent), #00c482) !important;
    color: #0d0f14 !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.3px !important;
    border: none !important;
    border-radius: var(--radius) !important;
    padding: 10px 24px !important;
    transition: opacity .2s, transform .1s !important;
}
.stButton > button:hover { opacity: .88 !important; transform: translateY(-1px) !important; }
.stButton > button:active { transform: translateY(0) !important; }

/* ── Info / warning boxes ── */
.ts-info {
    background: rgba(0,144,255,.08);
    border: 1px solid rgba(0,144,255,.25);
    border-left: 3px solid var(--accent2);
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 0.8rem;
    color: #a0b4cc;
    margin-top: 8px;
}
.ts-ended {
    background: rgba(0,229,160,.07);
    border: 1px solid rgba(0,229,160,.2);
    border-radius: var(--radius);
    padding: 18px 22px;
    text-align: center;
    margin-top: 16px;
}
.ts-ended h3 { font-family:'Syne',sans-serif; color:var(--accent); margin:0 0 6px; }
.ts-ended p  { color:var(--muted); font-size:0.85rem; margin:0; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
""",
    unsafe_allow_html=True,
)

# ── Run the UI ────────────────────────────────────────────────────────────────
render_ui()
