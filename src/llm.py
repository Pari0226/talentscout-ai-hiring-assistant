"""
llm.py — Thin wrapper around the Groq API (free, no credit card needed).
"""

from __future__ import annotations

import json
import os
from typing import List, Dict

from groq import Groq

_client = None
MODEL = "llama-3.3-70b-versatile"


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY environment variable is not set. "
                "Please add it to your .env file or export it before running."
            )
        _client = Groq(api_key=api_key)
    return _client


def chat(
    system: str,
    history: List[Dict[str, str]],
    user_message: str,
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> str:
    client = _get_client()
    messages = [{"role": "system", "content": system}]
    messages += history
    messages.append({"role": "user", "content": user_message})
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def generate_tech_questions(prompt: str) -> list[str]:
    client = _get_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a concise JSON generator. Output only valid JSON, nothing else."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=512,
        temperature=0.5,
    )
    raw = response.choices[0].message.content.strip()
    clean = raw.replace("```json", "").replace("```", "").strip()
    try:
        questions: list[str] = json.loads(clean)
        if isinstance(questions, list) and all(isinstance(q, str) for q in questions):
            return questions[:5]
    except (json.JSONDecodeError, ValueError):
        pass
    return [
        "Can you walk me through a recent technical challenge you solved and how you approached it?",
        "How do you ensure code quality and maintainability in your projects?",
        "Describe your experience with version control and collaborative development workflows.",
        "How do you stay current with new developments in your technology stack?",
    ]
