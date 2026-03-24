# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

AI Career Coach — a desktop app (macOS) that acts as a personal AI career coach for professionals and leaders. Uses PydanticAI for the AI agent, Flet for the UI, and SQLite for storage. See `README.md` for full user-facing documentation.

## CLI Coaching Mode

This project also functions as a Claude Code-powered career coach via skills and a shared database.

- `/coach-mode` — activates coaching persona for the full session (extended coaching)
- Individual skills (`/coach-goals`, `/coach-journal`, `/coach-reflect`, `/coach-memory`, `/coach-notes`, `/coach-commitments`, `/coach-nudges`, `/coach-check-in`, `/coach-weekly-review`) — work standalone for quick interactions

Both access the same SQLite database (`~/.ai_coach/data.db`) as the desktop app via `cli/db.py`.
Default mode is developer/coder — for working on the app itself. Coaching persona only activates when explicitly invoked.

## Tech Stack

- **UI**: Flet 0.81+ (Python, Flutter-backed) — `import flet as ft`, entry point `ft.run(main)`
- **AI Agent**: PydanticAI v1 (1.63+) — `Agent`, `RunContext`, tool functions, structured outputs
- **Storage**: SQLite via `aiosqlite` — DB at `~/.ai_coach/data.db`, FTS5 for memory search
- **Python**: 3.11+

## Commands

```bash
# First-time setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run (dev, with hot reload)
flet run main.py

# Run (direct)
python3 main.py

# Package for macOS (two-step process)
# Step 1: Generate the Flutter project (run once, or after dependency changes)
flet build macos
# Step 2: Build the .app from the generated Flutter project
cd build/flutter && flutter build macos --build-name 0.1.0 --no-version-check --suppress-analytics
# Step 3: Re-sign (needed if code signing is incomplete)
codesign --force --deep --sign - build/flutter/build/macos/Build/Products/Release/ai-coach.app
# Step 4: Copy to release folder
cp -R build/flutter/build/macos/Build/Products/Release/ai-coach.app release/
```

### Packaging notes

- `flet build macos` generates a Flutter project under `build/flutter/` but can hang with no output.
  Use `flutter build macos` from `build/flutter/` directly for verbose progress (`-v` flag).
- The build bundles all Python site-packages into `serious_python_darwin.framework` — this is slow (10+ min).
- After building, the app may fail to launch with `RBSRequestErrorDomain Code=5` — fix with `codesign --force --deep --sign -`.
- Release binary: `release/ai-coach.app`
- Flutter SDK must be on PATH: `export PATH="/Users/anchita/flutter/3.41.2/bin:$PATH"`

## Architecture

```
main.py                        → Flet app entry point, DB init, API key restore from settings
├── ui/
│   ├── theme.py               → Design system: colors, spacing, typography helpers, card/pill builders
│   ├── app.py                 → App shell: 7-tab sidebar, nudge banner, badge, CoachLoop startup
│   ├── views/
│   │   ├── chat.py            → Conversation sidebar + streaming chat, nudge-driven chats
│   │   ├── goals.py           → CRUD for career goals (priority pills, category badges, archive)
│   │   ├── memory.py          → Browse/search (FTS5)/add/delete memories, source badges
│   │   ├── diary.py           → Daily entries with mood tags, markdown rendering
│   │   ├── notes.py           → Reference notes: titled docs with FTS5 search, tags, CRUD
│   │   ├── notifications.py   → Pending nudges with actions + history, snooze/dismiss/talk
│   │   └── settings.py        → Provider config, model selection, proactive coaching settings
│   └── components/
│       ├── message_bubble.py  → Chat bubble with avatar, directional border radius, markdown
│       └── nudge_banner.py    → Top-of-page banner for latest pending nudge with actions
├── agent/
│   ├── coach.py               → create_coach_agent() and create_memory_extractor() factories
│   ├── proactive.py           → create_proactive_agent() — structured output (ProactiveDecision)
│   ├── tools.py               → 11 tools: goals, memories, diary, notes, today_info, commitments, followups
│   ├── prompts.py             → COACHING_SYSTEM_PROMPT, MEMORY_EXTRACTION_PROMPT, PROACTIVE_SYSTEM_PROMPT
│   └── models.py              → MemoryItem, MemoryExtraction, NudgeAction, ScheduledTask, ProactiveDecision
├── storage/
│   ├── database.py            → get_db(), close_db(), schema creation, FTS5 setup
│   ├── goals.py               → get_active(), get_all(), create(), update(), delete()
│   ├── memory.py              → get_all(), get_recent(), search(), create(), update(), delete()
│   ├── diary.py               → get_all(), get_recent(), get_by_date(), create(), update(), delete()
│   ├── notes.py               → get_all(), get_by_id(), search(), create(), update(), delete()
│   ├── conversations.py       → get_all(), create(), get_messages(), add_message(), delete()
│   ├── settings.py            → get(), set(), get_json(), set_json(), delete(), get_all()
│   ├── scheduled_tasks.py     → get_pending(), create(), update_status(), cancel()
│   ├── nudges.py              → get_pending(), create(), show(), snooze(), dismiss(), act_on()
│   └── commitments.py         → get_pending(), get_overdue(), create(), complete(), miss(), cancel()
└── services/
    ├── llm_manager.py         → detect_providers(), get_available_models(), get_default_model()
    ├── memory_curator.py      → curate_memories() + post-conversation follow-up scheduling
    ├── coach_loop.py          → CoachLoop: background heartbeat, proactive agent, nudge creation
    └── notifications.py       → macOS native notifications via osascript
```

## Design System (ui/theme.py)

All UI colors and styles are centralized in `ui/theme.py`. Every view imports from it.

- **Forces light mode** via `page.theme_mode = ft.ThemeMode.LIGHT`
- **Palette**: Indigo primary (`#4F46E5`), Teal accent (`#0D9488`), Slate neutrals
- **Helpers**: `heading()`, `subheading()`, `caption()`, `card()`, `pill()`, `section_divider()`
- **Constants**: `PAGE_PAD=28`, `SECTION_GAP=24`, `CARD_PAD=16`, `CARD_RADIUS=12`, `INPUT_RADIUS=10`

When adding new UI, always use `theme.card()` for card containers, `theme.pill()` for badges, and `theme.heading()`/`subheading()` for titles. Do not hardcode colors — use `theme.TEXT`, `theme.TEXT_SECONDARY`, `theme.BORDER`, etc.

## Key Patterns

- **All storage functions are async** — use `await` everywhere
- **Views extend `ft.Column`** and receive `page_ref: ft.Page` as constructor arg (stored as `self._page_ref`). They use `did_mount()` for initial async data loading.
- **All views are pre-created at startup** in `app.py._init_all_views()` so tab switching is instant
- **Background tasks** via `self._page_ref.run_task(coroutine)` — never block the UI
- **Memory curation is fire-and-forget** — runs in background when leaving chat tab, doesn't block navigation. Also schedules a 2-day follow-up task.
- **Proactive coach loop** — `CoachLoop` runs a background heartbeat (default 15 min). Each tick: checks settings/quiet hours, gathers context snapshot, calls proactive agent (structured output), creates nudges + scheduled tasks. Started after banner/badge refresh to avoid aiosqlite deadlock.
- **Nudge lifecycle**: pending → shown (banner displayed) → acted_on / snoozed / dismissed. Deduplication via `has_similar_pending()`.
- **Coach agent injects current date** into system prompt (not relying on tool call) so scheduled follow-ups use correct dates.
- **Agent tools use `RunContext[None]`** — tools access storage directly, no dependency injection needed
- **Default model auto-detection**: `get_default_model()` picks the first available model based on which API keys are present. No hardcoded provider preference.
- **API keys**: auto-detected from env vars (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`), also configurable in Settings UI and persisted to SQLite settings table. Restored into `os.environ` on startup.

## Database

SQLite at `~/.ai_coach/data.db` with tables: `goals`, `memories`, `diary_entries`, `notes`, `conversations`, `messages`, `settings`, `scheduled_tasks`, `nudges`, `commitments`. FTS5 virtual tables `memories_fts` and `notes_fts` for full-text search (Porter stemming tokenizer). Schema auto-created on first run. Delete the file to start fresh (must also delete `-shm` and `-wal` files when using WAL mode).

Coach loop logs to `~/.ai_coach/coach_loop.log` for debugging.

## Flet 0.81 API Gotchas

These are hard-won lessons from debugging. **Do not revert to the old patterns.**

| Old (broken/deprecated) | New (correct for 0.81) |
|---|---|
| `self.page = page` in ft.Column subclass | `self._page_ref = page_ref` — `.page` is read-only |
| `ft.colors.BLUE` | `ft.Colors.BLUE` (capitalized) |
| `ft.app(target=main)` | `ft.run(main)` |
| `ft.ElevatedButton(...)` | `ft.Button(...)` |
| `ft.padding.only(left=10)` | `ft.Padding(left=10)` |
| `ft.border.only(bottom=...)` | `ft.Border(bottom=...)` |
| `ft.border.all(1, color)` | `ft.Border.all(1, color)` |
| `ft.padding.symmetric(h=6, v=2)` | `ft.Padding(left=6, right=6, top=2, bottom=2)` |
| `ft.alignment.center_right` | `ft.Alignment(1, 0)` |
| `ft.margin.only(left=10)` | `ft.Margin(left=10, right=0, top=0, bottom=0)` |
| `Dropdown(on_change=handler)` | `Dropdown(on_select=handler)` |
| FTS5 `CREATE VIRTUAL TABLE IF NOT EXISTS` | Check `sqlite_master` first, then `CREATE VIRTUAL TABLE` |
| `PopupMenuItem(text="...")` | `PopupMenuItem(content="...")` |
| `executescript()` for schema init | Individual `execute()` calls (avoids WAL I/O errors) |
| `PRAGMA foreign_keys=ON` before schema | Move to **after** `_init_schema()` |
| SQLite `datetime('now')` for timestamp comparison | `datetime.now().isoformat()` (local time, consistent `T` separator) |

## PydanticAI v1 API Reference

- Agent creation: `Agent(model_string, system_prompt=..., tools=[...], output_type=...)`
- Model strings: `"anthropic:claude-sonnet-4-5"`, `"openai:gpt-4o"`, `"google-gla:gemini-2.0-flash"`
- Tools: plain async functions with `ctx: RunContext[None]` as first param, docstrings become tool descriptions
- Streaming: `async with agent.run_stream(prompt, message_history=...) as result:` then `async for chunk in result.stream_text(delta=True):`
- Structured output: `Agent(..., output_type=MyPydanticModel)`
- Message history: `ModelRequest(parts=[UserPromptPart(content=...)])`, `ModelResponse(parts=[TextPart(content=...)])`

## Current Status

**Working features:**
- Chat with streaming LLM responses, conversation history, conversation delete
- Goals CRUD with categories, priorities, archive/reactivate
- Memory browse, FTS5 search, manual add/delete, source badges
- Diary entries with mood tags, markdown rendering
- Settings with provider auto-detection, API key config, model selection
- Post-conversation memory curation (background, fire-and-forget)
- Light-mode design system with consistent styling across all views
- Proactive coaching: background heartbeat loop, LLM-driven nudges, self-scheduling
- Commitment tracking: agent tracks user commitments with due dates
- Notifications tab: pending nudges with Let's talk / Snooze / Dismiss actions
- Nudge banner: top-of-page banner showing latest pending nudge
- macOS native notifications via osascript
- Nudge-driven chats: "Let's talk" opens a pre-contextualized coaching conversation
- Proactive coaching settings: enable/disable, quiet hours, heartbeat interval
- Notes: persistent reference documents with titles, tags, FTS5 search, agent integration

**Not yet implemented (from original plan):**
- Ollama / local model support (PydanticAI supports it natively — easy to add)
- Vector search for memory (currently FTS5 only)
- Calendar integration via MCP
- Data export (goals/memories/diary as markdown)
- macOS packaging validated — see Commands section for build steps; release binary at `release/ai-coach.app`
