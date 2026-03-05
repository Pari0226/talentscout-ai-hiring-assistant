# 🎯 TalentScout — AI Hiring Assistant

A conversational AI chatbot that conducts **initial candidate screening** for technology placements.
Built with **Streamlit** (frontend) and the **Anthropic Claude API** (LLM backend).

---

## ✨ Features

| Feature | Detail |
|---|---|
| Guided info gathering | Collects name, email, phone, experience, position, location, tech stack — naturally, 1–2 fields at a time |
| Dynamic tech questions | Generates 4 tailored questions per candidate based on their declared stack + seniority |
| Context-aware dialogue | Full conversation history passed to the LLM on every turn |
| Fallback handling | Politely redirects off-topic input back to the screening flow |
| End-keyword detection | `bye / exit / quit / stop / done` gracefully closes the session |
| Data privacy | Emails are SHA-256 hashed before storage; only last-4 of phone is retained |
| Polished dark UI | Custom Streamlit CSS — `Syne` + `DM Sans` fonts, dark theme, progress tracker |

---

## 🗂️ Project Structure

```
talentscout/
├── app.py              # Streamlit entry point + global CSS
├── requirements.txt    # Python dependencies
├── .env.example        # API key template
├── data/               # Candidate records (auto-created, gitignored)
└── src/
    ├── __init__.py
    ├── prompts.py      # All system prompts + end-keyword logic
    ├── llm.py          # Anthropic API wrapper
    ├── session.py      # Streamlit session state management + data persistence
    ├── chat.py         # Conversation controller (state machine)
    └── ui.py           # Streamlit component rendering
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com)

### Steps

```bash
# 1. Clone / unzip the project
cd talentscout

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your API key
cp .env.example .env
# Edit .env and replace 'your_api_key_here' with your actual key

# 5. Run the app
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🧑‍💻 Usage Guide

1. **Greeting** — Aria (the bot) introduces herself and asks for your name.
2. **Info Gathering** — Answer questions about your email, phone, experience, desired role, location, and tech stack.
3. **Technical Assessment** — 4 tailored questions are generated and asked one by one.
4. **Wrap-up** — Aria thanks you and explains next steps.
5. **End anytime** — Type `bye`, `exit`, or `quit` to close the session early.

**New session** — Click *Start New Session* after the chat ends to reset.

---

## 🔧 Technical Details

### Libraries
| Library | Version | Purpose |
|---|---|---|
| `streamlit` | ≥ 1.35 | Frontend UI framework |
| `anthropic` | ≥ 0.28 | Claude API client |
| `python-dotenv` | ≥ 1.0 | `.env` file loading |

### Model
`claude-sonnet-4-20250514` — chosen for its strong instruction-following and conversational quality.

### Architecture Decisions
- **State machine** (`greeting → gather_info → tech_questions → wrap_up → ended`) keeps conversation flow predictable and testable.
- **Full history** is passed on every LLM call so Claude maintains context without a separate memory store.
- **Context hints** are injected as invisible suffixes to user messages (`[CONTEXT: ...]`) so the LLM always knows what to do next without breaking the chat illusion.
- **Regex extraction** opportunistically parses emails, phones, years-of-experience, and tech keywords from free-text — reducing the need for strict structured inputs.
- **Separate question-generation call** uses a minimal JSON-only system prompt for clean, parseable output.

---

## 💡 Prompt Design

### System Prompt (`SYSTEM_PROMPT`)
A single, authoritative persona prompt for the main conversation:
- Establishes **Aria** as a warm, professional TalentScout recruiter
- Defines the **exact 4-stage flow** she must follow
- Includes **strict guardrails**: no off-topic responses, no internal disclosure
- Specifies **output constraints**: ≤ 3 paragraphs, conversational tone

### Tech Question Prompt (`build_tech_question_prompt`)
Separate, minimal prompt injected into a JSON-generator system:
- Accepts tech stack + position + years of experience
- Requests exactly 4 questions across 4 axes: conceptual, practical, debugging, best-practice
- Calibrates difficulty to seniority (junior → conceptual; senior → architectural)
- Returns a clean JSON array for zero-friction parsing

### Context Hints
Invisible `[CONTEXT: ...]` suffixes appended to user messages guide the LLM at each state transition — telling it which fields are still missing, which question comes next, or when to wrap up — without polluting the visible conversation.

---

## 🔒 Data Privacy

- **Email**: Stored as a truncated SHA-256 hash only (first 16 hex chars).
- **Phone**: Only the last 4 digits are retained.
- **Storage**: JSON files in `data/` (local only). In production, replace with an encrypted DB.
- **Consent**: GDPR notice is displayed in the UI and available on request during the chat.
- **Retention**: The `data/` directory is excluded from version control via `.gitignore`.

---

## 🧩 Challenges & Solutions

| Challenge | Solution |
|---|---|
| Keeping LLM on-topic | Strong system prompt with explicit guardrails + fallback instruction |
| Parsing structured data from free text | Regex heuristics + opportunistic extraction on every turn |
| State-driven flow without breaking immersion | Invisible `[CONTEXT: ...]` hints appended to user messages |
| Reliable JSON from question generator | Dedicated JSON-only system prompt + defensive `json.loads` with fallback list |
| Streamlit re-rendering on input | `st.rerun()` after each message; state stored in `st.session_state` |

---

## 🌟 Optional Enhancements (implemented)

- ✅ Custom dark-mode UI with `Syne` / `DM Sans` fonts and animated progress tracker
- ✅ GDPR-compliant data handling with hashing
- ✅ Graceful end-keyword detection
- ✅ Modular, fully-documented codebase

---

## 📄 License

MIT — free to use, modify, and distribute.
