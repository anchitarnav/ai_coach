"""CRUD operations for conversations and messages."""

from storage.database import get_db


async def get_all(limit: int = 50) -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM conversations ORDER BY started_at DESC LIMIT ?",
        (limit,),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_by_id(conversation_id: int) -> dict | None:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def create(title: str = "New Conversation", model_used: str = "") -> int:
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO conversations (title, model_used) VALUES (?, ?)",
        (title, model_used),
    )
    await db.commit()
    return cursor.lastrowid


async def update_title(conversation_id: int, title: str) -> None:
    db = await get_db()
    await db.execute(
        "UPDATE conversations SET title = ? WHERE id = ?",
        (title, conversation_id),
    )
    await db.commit()


async def delete(conversation_id: int) -> None:
    db = await get_db()
    await db.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    await db.commit()


# --- Messages ---


async def get_messages(conversation_id: int) -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (conversation_id,),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def add_message(conversation_id: int, role: str, content: str) -> int:
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
        (conversation_id, role, content),
    )
    await db.commit()
    return cursor.lastrowid


async def get_today_conversation() -> dict | None:
    """Get or return None for today's daily conversation."""
    db = await get_db()
    cursor = await db.execute(
        """SELECT * FROM conversations
           WHERE date(started_at) = date('now')
           ORDER BY started_at ASC
           LIMIT 1"""
    )
    row = await cursor.fetchone()
    return dict(row) if row else None
