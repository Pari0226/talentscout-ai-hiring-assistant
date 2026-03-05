"""
session.py — Manages Streamlit session state for TalentScout.

Encapsulates all mutable state so app.py / ui.py stay clean.
"""

from __future__ import annotations

import json
import datetime
import hashlib
from pathlib import Path
from typing import Any

import streamlit as st

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


# ── Defaults ──────────────────────────────────────────────────────────────────
_DEFAULTS: dict[str, Any] = {
    "stage": "greeting",
    "history": [],           # list of {role, content} dicts for LLM
    "display": [],           # list of {role, content} dicts for UI rendering
    "candidate": {
        "full_name": "",
        "email": "",
        "phone": "",
        "experience_years": "",
        "desired_position": "",
        "location": "",
        "tech_stack": "",
    },
    "tech_questions": [],    # generated question list
    "q_index": 0,            # which question we're on
    "answered_qs": [],       # candidate answers to tech questions
    "initialized": False,
}


def init() -> None:
    """Initialise session state with defaults (idempotent)."""
    for key, value in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset() -> None:
    """Reset all session state to defaults."""
    for key, value in _DEFAULTS.items():
        st.session_state[key] = value if not isinstance(value, (dict, list)) else type(value)(value)
    st.session_state["candidate"] = {k: "" for k in _DEFAULTS["candidate"]}


def add_message(role: str, content: str) -> None:
    """Append a message to both the LLM history and the display list."""
    msg = {"role": role, "content": content}
    st.session_state.history.append(msg)
    st.session_state.display.append(msg)


def save_candidate_data() -> str:
    """
    Persist candidate info + answers to a JSON file in data/.
    Returns the file path (for logging / demo purposes only).

    Data privacy: file names are hashed so no PII leaks into filenames.
    In production, replace with encrypted DB writes.
    """
    candidate = st.session_state.candidate
    answers = st.session_state.answered_qs
    questions = st.session_state.tech_questions

    record = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "candidate": {
            # Mask email partially for storage demo
            "full_name": candidate.get("full_name", ""),
            "email_hash": hashlib.sha256(
                candidate.get("email", "").lower().encode()
            ).hexdigest()[:16],
            "phone_last4": candidate.get("phone", "")[-4:] if candidate.get("phone") else "",
            "experience_years": candidate.get("experience_years", ""),
            "desired_position": candidate.get("desired_position", ""),
            "location": candidate.get("location", ""),
            "tech_stack": candidate.get("tech_stack", ""),
        },
        "technical_assessment": [
            {"question": q, "answer": a}
            for q, a in zip(questions, answers)
        ],
    }

    filename = DATA_DIR / f"candidate_{record['timestamp'][:10]}_{record['candidate']['email_hash']}.json"
    with open(filename, "w") as f:
        json.dump(record, f, indent=2)

    return str(filename)


# ── Stage helpers ──────────────────────────────────────────────────────────────
STAGE_LABELS = {
    "greeting":      "Welcome",
    "gather_info":   "Profile",
    "tech_questions": "Assessment",
    "wrap_up":       "Wrap-up",
    "ended":         "Complete",
}

STAGE_ORDER = ["greeting", "gather_info", "tech_questions", "wrap_up", "ended"]


def stage_progress() -> tuple[int, int]:
    """Return (current_index, total_stages)."""
    current = st.session_state.get("stage", "greeting")
    idx = STAGE_ORDER.index(current) if current in STAGE_ORDER else 0
    return idx, len(STAGE_ORDER)
