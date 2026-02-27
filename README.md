# AI Career Coach

A desktop application (macOS) that acts as a personal AI career coach. Built for professionals and leaders, it provides daily actionable advice, maintains persistent memory of your context and learnings, and connects everything back to your long-term career goals.

## What It Does

- **Daily coaching conversations** — Ask "What should I do today?" and get structured advice tied to your goals, recent context, and diary reflections
- **Proactive coaching** — The coach doesn't just wait for you. It periodically checks your goals and commitments, and sends nudges when something needs attention — overdue commitments, follow-ups from past conversations, or just a check-in when you've been quiet
- **Commitment tracking** — When you tell the coach you'll do something, it tracks it automatically and follows up later
- **Notifications** — In-app nudge banner, dedicated Notifications tab, and macOS native notifications. Each nudge offers "Let's talk" (opens a contextual chat), "Snooze", or "Dismiss"
- **Goal tracking** — Define and manage long-term career goals with categories and priorities
- **Persistent memory** — The coach remembers key decisions, insights, and context across sessions. Memories are auto-curated from conversations and can also be added manually
- **Diary entries** — Free-form journaling with mood tracking; the coach draws on recent entries for context
- **Multi-provider LLM support** — Use Claude, OpenAI, or Gemini. Switch models anytime from Settings

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| UI | [Flet](https://flet.dev) (Python) | Native desktop app via Flutter rendering |
| AI Agent | [PydanticAI](https://ai.pydantic.dev) v1 | LLM orchestration, tool calling, structured outputs |
| Storage | SQLite via [aiosqlite](https://github.com/omnilib/aiosqlite) | Local database with FTS5 full-text search |
| Python | 3.11+ | Async throughout |

## Prerequisites

- **Python 3.11+** — Check with `python3 --version`
- **An LLM API key** — At least one of:
  - `ANTHROPIC_API_KEY` for Claude models
  - `OPENAI_API_KEY` for OpenAI models
  - `GOOGLE_API_KEY` for Gemini models

## Setup

```bash
# Clone the repository
git clone <repo-url>
cd ai_coach

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Set your API key

Either export it in your shell:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
# or
export OPENAI_API_KEY=sk-...
# or
export GOOGLE_API_KEY=AI...
```

Or configure it in the app's **Settings** view after launching.

## Running the App

### Development mode (with hot reload)

```bash
source .venv/bin/activate
flet run main.py
```

### Direct run

```bash
source .venv/bin/activate
python3 main.py
```

### Package as a macOS app

```bash
source .venv/bin/activate
flet build macos
```

This produces a standalone `.app` bundle you can double-click to open.

## Project Structure

```
ai_coach/
├── main.py                    # App entry point — initializes DB, restores keys, launches Flet
├── pyproject.toml             # Project metadata and dependencies
├── requirements.txt           # Pinned dependencies for reproducible installs
│
├── ui/                        # Flet UI layer
│   ├── app.py                 # App shell — 6-tab sidebar, nudge banner, coach loop startup
│   ├── views/
│   │   ├── chat.py            # Coaching conversation with streaming LLM responses
│   │   ├── goals.py           # CRUD for long-term career goals
│   │   ├── memory.py          # Browse, search (FTS5), add/delete memories
│   │   ├── diary.py           # Daily journal entries with mood tagging
│   │   ├── notifications.py   # Pending nudges with actions + notification history
│   │   └── settings.py        # LLM provider config, model selection, proactive coaching settings
│   └── components/
│       ├── message_bubble.py  # Chat message bubble (user/assistant, markdown rendering)
│       ├── nudge_banner.py    # Top-of-page banner for latest pending nudge
│       └── sidebar.py         # NavigationRail sidebar with 6 destinations
│
├── agent/                     # AI agent layer (PydanticAI)
│   ├── coach.py               # Agent factories — coaching agent + memory extractor
│   ├── proactive.py           # Proactive agent — structured output for nudge/schedule decisions
│   ├── tools.py               # 9 agent tools — goals, memories, diary, commitments, follow-ups
│   ├── prompts.py             # System prompts for coaching, memory extraction, proactive engine
│   └── models.py              # Pydantic models for structured outputs
│
├── storage/                   # Data persistence layer (async SQLite)
│   ├── database.py            # Connection management, schema creation, FTS5 setup
│   ├── goals.py               # Goals CRUD (create, read, update, archive, delete)
│   ├── memory.py              # Memory CRUD + FTS5 full-text search
│   ├── diary.py               # Diary entries CRUD
│   ├── conversations.py       # Conversations and messages CRUD
│   ├── settings.py            # Key-value settings store (JSON support)
│   ├── scheduled_tasks.py     # Proactive coach wake-up tasks CRUD
│   ├── nudges.py              # Nudge notifications CRUD with lifecycle management
│   └── commitments.py         # User commitment tracking CRUD
│
└── services/                  # Business logic
    ├── llm_manager.py         # Provider detection, model listing, API key management
    ├── memory_curator.py      # Post-conversation memory extraction + follow-up scheduling
    ├── coach_loop.py          # Background heartbeat loop — runs proactive agent periodically
    └── notifications.py       # macOS native notifications via osascript
```

## Architecture Overview

### How the layers connect

```
User ←→ Flet UI (ui/) ←→ PydanticAI Agent (agent/) ←→ LLM Provider (Claude/OpenAI/Gemini)
                ↕                    ↕
           SQLite DB (storage/) ← shared async access
```

1. **UI layer** (`ui/`) renders views and handles user interaction. Each view is a Flet `Column` subclass with a `did_mount()` lifecycle hook for async initialization.

2. **Agent layer** (`agent/`) defines two PydanticAI agents:
   - **Coaching agent** — interactive, with 9 tools for accessing goals, memories, diary, commitments, and scheduling follow-ups
   - **Proactive agent** — background, with structured output (`ProactiveDecision`) that decides what nudges to send and what future wake-ups to schedule

3. **Storage layer** (`storage/`) provides async CRUD functions for all data. Every function uses `await get_db()` to access the shared SQLite connection. The `memories` table has a companion `memories_fts` FTS5 virtual table for full-text search.

4. **Services layer** (`services/`) contains business logic that orchestrates agent + storage:
   - `llm_manager.py` scans environment variables for API keys and lists available models
   - `memory_curator.py` runs a separate PydanticAI agent to extract memories from completed conversations, and schedules a 2-day follow-up task
   - `coach_loop.py` runs a background heartbeat that periodically calls the proactive agent to generate nudges
   - `notifications.py` sends macOS native notifications via osascript

### Data flow: Daily coaching

```
User: "What should I do today?"
  → Chat view sends message to coaching agent
  → Agent calls tools: get_active_goals(), get_recent_memories(), get_recent_diary_entries()
  → Agent generates streaming response using goal/memory/diary context
  → Response streams into the chat UI in real time
  → When user leaves chat, memory_curator extracts key insights → saves to memories table
```

### Data flow: Proactive coaching

```
Background (every 15 min):
  → CoachLoop._tick() gathers context: goals, commitments, memories, diary, fired tasks
  → Proactive agent decides: send nudges? schedule future tasks? discard stale tasks?
  → Nudges created in DB → macOS notification sent → in-app banner + badge updated
  → User clicks "Let's talk" → opens new chat pre-loaded with nudge context
```

### Database

SQLite database stored at `~/.ai_coach/data.db`. Created automatically on first run.

**Tables:** `goals`, `memories`, `diary_entries`, `conversations`, `messages`, `settings`, `scheduled_tasks`, `nudges`, `commitments`

**FTS5:** `memories_fts` virtual table (Porter stemming tokenizer) enables full-text search over memory content and tags.

### LLM Provider Support

PydanticAI model strings determine the provider:

| Provider | Model string example | Env var |
|----------|---------------------|---------|
| Anthropic | `anthropic:claude-sonnet-4-5` | `ANTHROPIC_API_KEY` |
| OpenAI | `openai:gpt-4o` | `OPENAI_API_KEY` |
| Google Gemini | `google-gla:gemini-2.0-flash` | `GOOGLE_API_KEY` |

Keys are auto-detected from environment variables at startup. Saved keys (via Settings UI) are restored on subsequent launches.

## Key Design Decisions

1. **Two agents, one coaching persona** — An interactive coaching agent (with tools) for conversations, and a proactive agent (structured output) for background nudge decisions. Both share the same coaching personality.

2. **LLM-as-scheduler** — The proactive agent decides when to wake up, what to check on, and whether to nudge the user. No hardcoded rules — the LLM reasons about context to make scheduling decisions.

3. **Tools over context stuffing** — The agent fetches what it needs via tool calls instead of dumping everything into every prompt. Saves tokens, scales to large memory stores.

4. **Semi-automatic memory curation** — The agent extracts memories from conversations automatically, but users can always review, edit, or delete them.

5. **Async everything** — All storage and agent calls are async. The UI stays responsive during LLM streaming via Flet's `page.run_task()`.

6. **Local-first** — No server, no cloud storage. All data lives in a single SQLite file on your machine.

## Troubleshooting

**App doesn't start:** Make sure you activated the venv (`source .venv/bin/activate`) and installed dependencies.

**"No models available" in Settings:** No API keys detected. Set one via environment variable or the Settings UI.

**Chat shows "Error: ...":** Usually an API key issue. Check that your key is valid and the selected model matches your provider.

**Database issues:** Delete `~/.ai_coach/data.db` (and `data.db-shm`, `data.db-wal`) to start fresh. The schema is recreated automatically.

**Proactive coaching not working:** Check `~/.ai_coach/coach_loop.log` for errors. Verify an API key is configured and proactive coaching is enabled in Settings.
