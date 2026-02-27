"""SQLite database connection, schema creation, and migrations."""

import aiosqlite
import os
from pathlib import Path

DB_DIR = Path.home() / ".ai_coach"
DB_PATH = DB_DIR / "data.db"

_connection: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    global _connection
    if _connection is None:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        _connection = await aiosqlite.connect(str(DB_PATH))
        _connection.row_factory = aiosqlite.Row
        await _connection.execute("PRAGMA journal_mode=WAL")
        await _init_schema(_connection)
        await _connection.execute("PRAGMA foreign_keys=ON")
    return _connection


async def close_db():
    global _connection
    if _connection is not None:
        await _connection.close()
        _connection = None


_SCHEMA_STATEMENTS = [
    """CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        category TEXT NOT NULL DEFAULT '',
        priority INTEGER NOT NULL DEFAULT 3,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN NOT NULL DEFAULT 1
    )""",
    """CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL DEFAULT 'New Conversation',
        started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        model_used TEXT NOT NULL DEFAULT ''
    )""",
    """CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
        role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
        content TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        source TEXT NOT NULL DEFAULT 'user_added',
        tags TEXT NOT NULL DEFAULT '',
        relevance_score REAL NOT NULL DEFAULT 0.5,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        conversation_id INTEGER REFERENCES conversations(id) ON DELETE SET NULL
    )""",
    """CREATE TABLE IF NOT EXISTS diary_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        content TEXT NOT NULL,
        mood TEXT NOT NULL DEFAULT '',
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL DEFAULT ''
    )""",
    "CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_memories_source ON memories(source)",
    "CREATE INDEX IF NOT EXISTS idx_goals_active ON goals(is_active)",
    "CREATE INDEX IF NOT EXISTS idx_diary_date ON diary_entries(date)",
    """CREATE TABLE IF NOT EXISTS scheduled_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        wake_at TIMESTAMP NOT NULL,
        context TEXT NOT NULL DEFAULT '',
        source TEXT NOT NULL DEFAULT 'heartbeat',
        related_goal_id INTEGER REFERENCES goals(id) ON DELETE SET NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        fired_at TIMESTAMP
    )""",
    "CREATE INDEX IF NOT EXISTS idx_tasks_wake ON scheduled_tasks(status, wake_at)",
    """CREATE TABLE IF NOT EXISTS nudges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT NOT NULL,
        chat_context TEXT NOT NULL DEFAULT '',
        priority TEXT NOT NULL DEFAULT 'gentle',
        status TEXT NOT NULL DEFAULT 'pending',
        source_task_id INTEGER REFERENCES scheduled_tasks(id) ON DELETE SET NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        shown_at TIMESTAMP,
        acted_at TIMESTAMP,
        snoozed_until TIMESTAMP,
        conversation_id INTEGER REFERENCES conversations(id) ON DELETE SET NULL
    )""",
    "CREATE INDEX IF NOT EXISTS idx_nudges_status ON nudges(status)",
    """CREATE TABLE IF NOT EXISTS commitments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        what TEXT NOT NULL,
        due_date DATE,
        status TEXT NOT NULL DEFAULT 'pending',
        conversation_id INTEGER REFERENCES conversations(id) ON DELETE SET NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP
    )""",
]


async def _init_schema(db: aiosqlite.Connection):
    for stmt in _SCHEMA_STATEMENTS:
        await db.execute(stmt)

    # FTS5 virtual table for memory search
    # Check if it exists first (CREATE ... IF NOT EXISTS doesn't work for virtual tables in all versions)
    cursor = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='memories_fts'"
    )
    if await cursor.fetchone() is None:
        await db.execute("""
            CREATE VIRTUAL TABLE memories_fts USING fts5(
                content,
                tags,
                content_rowid='id',
                tokenize='porter'
            )
        """)
        # Populate FTS from any existing data
        await db.execute("""
            INSERT INTO memories_fts(rowid, content, tags)
            SELECT id, content, tags FROM memories
        """)

    await db.commit()
