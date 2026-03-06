"""
ui.py — Streamlit UI components for TalentScout Hiring Assistant.
"""

from __future__ import annotations

import streamlit as st

from .session import init, reset, stage_progress, STAGE_ORDER, STAGE_LABELS, add_message
from .chat import handle_initial_greeting, handle_user_input


def _render_chat() -> None:
    st.markdown('<div class="ts-chat-wrap">', unsafe_allow_html=True)
    for msg in st.session_state.display:
        role = msg["role"]
        content = msg["content"].replace("\n", "<br>")
        avatar_html = (
            '<div class="ts-avatar bot">A</div>'
            if role == "assistant"
            else '<div class="ts-avatar user">U</div>'
        )
        bubble_class = "bot" if role == "assistant" else "user"
        st.markdown(
            f"""
            <div class="ts-bubble {bubble_class}">
                {avatar_html}
                <div class="ts-msg {bubble_class}">{content}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def _render_progress() -> None:
    current_idx, total = stage_progress()
    bars = ""
    for i, stage in enumerate(STAGE_ORDER):
        if i < current_idx:
            cls = "done"
        elif i == current_idx:
            cls = "active"
        else:
            cls = ""
        bars += f'<div class="ts-step {cls}"></div>'
    label = STAGE_LABELS.get(st.session_state.stage, "")
    st.markdown(
        f'<div class="ts-progress">{bars}<span class="ts-step-label">{label}</span></div>',
        unsafe_allow_html=True,
    )


def _render_header() -> None:
    st.markdown(
        """
        <div class="ts-header">
            <div>
                <div class="ts-logo">TalentScout</div>
                <div class="ts-tagline">AI Hiring Assistant · Technology Placements</div>
            </div>
            <div class="ts-badge">● Live</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_ui() -> None:
    init()

    # ── Sidebar ────────────────────────────────────────────────────────────────
    st.sidebar.title("🎯 Candidate Profile")
    candidate = st.session_state.get("candidate", {})
    fields = {
        "Name": candidate.get("full_name"),
        "Email": candidate.get("email"),
        "Phone": candidate.get("phone"),
        "Experience": candidate.get("experience_years"),
        "Desired Role": candidate.get("desired_position"),
        "Location": candidate.get("location"),
        "Tech Stack": candidate.get("tech_stack"),
    }
    for label, value in fields.items():
        if value:
            st.sidebar.markdown(f"**{label}:** {value}")
        else:
            st.sidebar.markdown(f"**{label}:** _Not provided yet_")
    st.sidebar.markdown("---")
    st.sidebar.caption("Data handled per GDPR")

    _render_header()
    _render_progress()

    # ── Greeting: only fire if display is truly empty ──────────────────────────
    # The key insight: check len(display) == 0 as the ONLY guard.
    # We do NOT rely on st.session_state.initialized because Streamlit Cloud
    # can rerun the script while session state is still being established.
    # Instead we use a st.session_state key that is set atomically WITH
    # the message being appended, so if display has content, we never re-greet.
    if len(st.session_state.display) == 0:
        if not st.session_state.get("greeting_in_progress", False):
            st.session_state["greeting_in_progress"] = True
            st.session_state.initialized = True
            with st.spinner("Connecting to Aria…"):
                try:
                    greeting = handle_initial_greeting()
                    add_message("assistant", greeting)
                    st.session_state["greeting_in_progress"] = False
                except EnvironmentError as e:
                    st.session_state.initialized = False
                    st.session_state["greeting_in_progress"] = False
                    st.error(str(e))
                    st.markdown(
                        '<div class="ts-info">🔑 Set your <code>GROQ_API_KEY</code> '
                        "in a <code>.env</code> file or as an environment variable, then reload.</div>",
                        unsafe_allow_html=True,
                    )
                    return

    _render_chat()

    if st.session_state.stage == "ended":
        st.markdown(
            """
            <div class="ts-ended">
                <h3>✅ Screening Complete</h3>
                <p>Your responses have been recorded. The TalentScout team will be in touch shortly.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Start New Session", use_container_width=True):
                reset()
                st.rerun()
        return

    col_input, col_send = st.columns([5, 1])
    with col_input:
        user_input = st.text_input(
            label="Your message",
            label_visibility="collapsed",
            placeholder="Type your reply…",
            key="user_input_field",
        )
    with col_send:
        send_clicked = st.button("Send", use_container_width=True)

    if send_clicked and user_input.strip():
        with st.spinner("Aria is typing…"):
            handle_user_input(user_input.strip())
        st.rerun()

    st.markdown(
        '<div class="ts-info">🔒 Your data is handled securely and in compliance with GDPR. '
        "Type <strong>exit</strong> or <strong>bye</strong> at any time to end the session.</div>",
        unsafe_allow_html=True,
    )