"""
chat.py — Conversation controller for TalentScout.

Bridges user input → LLM → session state updates.
This is the 'brain' of the app; UI code stays thin.
"""

from __future__ import annotations

import re
import streamlit as st

from .llm import chat, generate_tech_questions
from .prompts import (
    SYSTEM_PROMPT,
    build_tech_question_prompt,
    FALLBACK_MESSAGE,
    is_end_keyword,
)
from .session import add_message, save_candidate_data


# ── Info-extraction helpers ────────────────────────────────────────────────────

def _extract_email(text: str) -> str:
    m = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    return m.group(0) if m else ""


def _extract_phone(text: str) -> str:
    m = re.search(r"[\+\d][\d\s\-\(\)]{7,}", text)
    return m.group(0).strip() if m else ""


def _extract_years(text: str) -> str:
    m = re.search(r"\b(\d{1,2})\s*(?:years?|yrs?|yr|months?|mos?)", text, re.IGNORECASE)
    if m:
        return m.group(0)  # e.g. "2 months"
    m2 = re.search(r"\b(\d{1,2})\b", text)
    return m2.group(1) if m2 else ""


def _try_fill_candidate(user_input: str, candidate: dict) -> None:
    """Opportunistically extract structured data from free-text."""
    if not candidate.get("email"):
        e = _extract_email(user_input)
        if e:
            candidate["email"] = e

    if not candidate.get("phone"):
        p = _extract_phone(user_input)
        if p:
            candidate["phone"] = p

    if not candidate.get("experience_years"):
        y = _extract_years(user_input)
        if y:
            candidate["experience_years"] = y


# ── Stage transition helpers ───────────────────────────────────────────────────

def _maybe_advance_stage(assistant_reply: str, user_input: str) -> None:
    """Heuristically decide when to advance the conversation stage."""
    stage = st.session_state.stage

    if stage == "gather_info":
        c = st.session_state.candidate
        filled = all([
            c.get("full_name"),
            c.get("email"),
            c.get("experience_years"),
            c.get("desired_position"),
            c.get("tech_stack"),
        ])
        if filled and not st.session_state.tech_questions:
            _trigger_question_generation()

    elif stage == "tech_questions":
        # FIX: Only advance when ALL questions answered, not after just one
        q_index = st.session_state.q_index
        total = len(st.session_state.tech_questions)
        if total > 0 and q_index >= total:
            st.session_state.stage = "wrap_up"


def _trigger_question_generation() -> None:
    """Generate tech questions and kick off the assessment stage."""
    c = st.session_state.candidate
    prompt = build_tech_question_prompt(
        tech_stack=c.get("tech_stack", ""),
        position=c.get("desired_position", ""),
        experience_years=c.get("experience_years", ""),
    )
    questions = generate_tech_questions(prompt)
    st.session_state.tech_questions = questions
    st.session_state.q_index = 0
    st.session_state.stage = "tech_questions"


def _update_candidate_from_context(history: list[dict]) -> None:
    """Parse conversation history to fill candidate profile fields."""
    c = st.session_state.candidate

    for msg in history:
        if msg["role"] == "user":
            _try_fill_candidate(msg["content"], c)

    # Name: first short user message that looks like a name
    if not c.get("full_name") and len(history) >= 2:
        first_user = next((m["content"] for m in history if m["role"] == "user"), "")
        words = first_user.strip().split()
        if 1 <= len(words) <= 5 and all(w[0].isupper() or w[0].isalpha() for w in words if w):
            c["full_name"] = first_user.strip().title()

    # Tech stack — expanded to include NLP, OpenCV, LLM, ML etc.
    if not c.get("tech_stack"):
        tech_keywords = re.compile(
            r"\b(python|javascript|typescript|react|vue|angular|node|django|flask|"
            r"fastapi|spring|java|kotlin|swift|rust|go|golang|c\+\+|c#|dotnet|"
            r"ruby|rails|php|laravel|mysql|postgres|postgresql|mongodb|redis|"
            r"docker|kubernetes|aws|gcp|azure|terraform|graphql|rest|sql|nosql|"
            r"pytorch|tensorflow|scikit-learn|scikit|pandas|numpy|spark|kafka|"
            r"elasticsearch|nlp|opencv|llm|huggingface|langchain|streamlit|"
            r"machine learning|deep learning|neural network|transformers|"
            r"prompt engineering|generative ai)\b",
            re.IGNORECASE,
        )
        for msg in history:
            if msg["role"] == "user":
                techs = tech_keywords.findall(msg["content"])
                if techs:
                    c["tech_stack"] = ", ".join(dict.fromkeys(t.lower() for t in techs))
                    break

    # Desired position — broad pattern to catch "AI/ML intern", "internship" etc.
    if not c.get("desired_position"):
        pos_pattern = re.compile(
            r"\b(software engineer|frontend|backend|full.?stack|data scientist|"
            r"ml engineer|ai.?ml|ai\/ml|machine learning engineer|"
            r"devops|cloud engineer|mobile developer|android|ios|"
            r"product manager|qa engineer|site reliability|sre|"
            r"intern|internship|developer|programmer|analyst|architect)\b",
            re.IGNORECASE,
        )
        for msg in history:
            if msg["role"] == "user":
                m = pos_pattern.search(msg["content"])
                if m:
                    c["desired_position"] = msg["content"].strip()[:80]
                    break

    # Location — "based in X", city names, Indian cities
    if not c.get("location"):
        loc_explicit = re.compile(
            r"(?:based in|located in|from|living in|currently in|currently at)\s+([A-Za-z\s,]+?)(?:\.|,|\n|$)",
            re.IGNORECASE,
        )
        loc_city = re.compile(
            r"\b(gurgaon|gurugram|haryana|delhi|mumbai|bangalore|bengaluru|hyderabad|"
            r"chennai|pune|kolkata|noida|india|remote|usa|uk|canada|australia|"
            r"new york|san francisco|london|berlin|singapore)\b",
            re.IGNORECASE,
        )
        for msg in history:
            if msg["role"] == "user":
                m = loc_explicit.search(msg["content"])
                if m:
                    c["location"] = m.group(1).strip()[:60]
                    break
                m2 = loc_city.search(msg["content"])
                if m2:
                    c["location"] = msg["content"].strip()[:60]
                    break


# ── Main entry points ──────────────────────────────────────────────────────────

def handle_initial_greeting() -> str:
    """Generate the opening bot message."""
    opening = chat(
        system=SYSTEM_PROMPT,
        history=[],
        user_message="[SYSTEM: Start the conversation. Greet the candidate warmly, introduce yourself as Aria from TalentScout, explain the purpose of this chat (initial screening), and ask for their full name to get started.]",
        max_tokens=256,
        temperature=0.8,
    )
    st.session_state.stage = "gather_info"
    return opening


def handle_user_input(user_input: str) -> str:
    """Process a user message and return the assistant reply."""

    # ── 1. Already ended ─────────────────────────────────────────────────────
    if st.session_state.stage == "ended":
        message = "The screening process has already been completed. Thank you for your time."
        add_message("user", user_input)
        add_message("assistant", message)
        return message

    # ── 2. End-keyword check ──────────────────────────────────────────────────
    if is_end_keyword(user_input):
        save_candidate_data()
        farewell = chat(
            system=SYSTEM_PROMPT,
            history=st.session_state.history,
            user_message=user_input,
            max_tokens=200,
        )
        add_message("user", user_input)
        add_message("assistant", farewell)
        st.session_state.stage = "ended"
        return farewell

    # ── 3. Input validation (gather_info only) ────────────────────────────────
    if st.session_state.stage == "gather_info":
        if "@" in user_input:
            if not re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', user_input.strip()):
                message = "That doesn't look like a valid email address. Could you please enter a valid one? (e.g. name@example.com)"
                add_message("user", user_input)
                add_message("assistant", message)
                return message

        stripped = user_input.strip()
        if re.match(r'^[\d\s\+\-\(\)]+$', stripped):
            digits = re.sub(r'\D', '', stripped)
            if len(digits) > 0 and len(digits) != 10:
                message = "Please provide a valid 10-digit phone number (digits only)."
                add_message("user", user_input)
                add_message("assistant", message)
                return message

    # ── 4. Extract structured data ────────────────────────────────────────────
    _update_candidate_from_context(st.session_state.history + [{"role": "user", "content": user_input}])

    # ── 5. Build context hint ─────────────────────────────────────────────────
    stage = st.session_state.stage
    context_hint = _build_context_hint(stage, user_input)

    # ── 6. Call LLM ──────────────────────────────────────────────────────────
    try:
        reply = chat(
            system=SYSTEM_PROMPT,
            history=st.session_state.history,
            user_message=user_input + context_hint,
            max_tokens=400,
        )
    except Exception as exc:
        reply = f"⚠️ I encountered a technical issue. Please try again. (Error: {exc})"

    # ── 7. Update history ────────────────────────────────────────────────────
    add_message("user", user_input)
    add_message("assistant", reply)

    # ── 8. Record tech answers ───────────────────────────────────────────────
    if stage == "tech_questions":
        st.session_state.answered_qs.append(user_input)
        st.session_state.q_index += 1

    # ── 9. Stage transitions ─────────────────────────────────────────────────
    _maybe_advance_stage(reply, user_input)

    # ── 10. Save data at wrap-up ──────────────────────────────────────────────
    if st.session_state.stage == "wrap_up" and stage != "wrap_up":
        try:
            save_candidate_data()
        except Exception:
            pass

    # ── 11. Mark ended after wrap-up ──────────────────────────────────────────
    if stage == "wrap_up":
        st.session_state.stage = "ended"

    return reply


def _build_context_hint(stage: str, user_input: str) -> str:
    """Append invisible context hints to guide the LLM at each stage."""
    c = st.session_state.candidate

    if stage == "gather_info":
        if not c.get("email"):
            return "\n\n[CONTEXT: Ask for the candidate's email address.]"
        elif not c.get("phone"):
            return "\n\n[CONTEXT: Ask for the candidate's phone number (10 digits).]"
        else:
            missing = [k for k, v in c.items() if not v and k not in ("email", "phone")]
            if missing:
                fields = ", ".join(missing[:3])
                return (
                    f"\n\n[CONTEXT: Still need: {fields}. "
                    f"Continue gathering info naturally. Do NOT list all fields at once.]"
                )
            else:
                return "\n\n[CONTEXT: All candidate info gathered. Transition smoothly into the technical assessment phase.]"

    elif stage == "tech_questions":
        questions = st.session_state.tech_questions
        q_index = st.session_state.q_index
        total = len(questions)
        if q_index < total:
            next_q = questions[q_index]
            return (
                f"\n\n[CONTEXT: Acknowledge their answer briefly (1 sentence), "
                f"then ask technical question {q_index + 1}/{total}: \"{next_q}\"]"
            )
        else:
            return "\n\n[CONTEXT: All technical questions answered. Transition to wrap-up: thank the candidate warmly, summarise next steps.]"

    elif stage == "wrap_up":
        return (
            "\n\n[CONTEXT: Wrap up the interview. Thank the candidate warmly. "
            "Explain that the TalentScout team will review within 3–5 business days "
            "and contact them via email. Wish them well.]"
        )

    return ""