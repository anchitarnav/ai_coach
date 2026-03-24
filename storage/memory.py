"""CRUD operations for permanent memory entries."""

from storage.database import get_db


async def get_all(limit: int = 100, offset: int = 0) -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM memories ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_recent(days: int = 14, min_relevance: float = 0.0) -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        """SELECT * FROM memories
           WHERE created_at >= datetime('now', ?)
             AND relevance_score >= ?
           ORDER BY relevance_score DESC, created_at DESC""",
        (f"-{days} days", min_relevance),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def search(query: str, limit: int = 20) -> list[dict]:
    db = await get_db()
    # Quote the query so FTS5 treats it as literal tokens, not column references
    safe_query = '"' + query.replace('"', '""') + '"'
    cursor = await db.execute(
        """SELECT m.*, rank
           FROM memories_fts fts
           JOIN memories m ON m.id = fts.rowid
           WHERE memories_fts MATCH ?
           ORDER BY rank
           LIMIT ?""",
        (safe_query, limit),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def create(
    content: str,
    source: str = "user_added",
    tags: str = "",
    relevance_score: float = 0.5,
    conversation_id: int | None = None,
) -> int:
    db = await get_db()
    cursor = await db.execute(
        """INSERT INTO memories (content, source, tags, relevance_score, conversation_id)
           VALUES (?, ?, ?, ?, ?)""",
        (content, source, tags, relevance_score, conversation_id),
    )
    # Update FTS index
    await db.execute(
        "INSERT INTO memories_fts(rowid, content, tags) VALUES (?, ?, ?)",
        (cursor.lastrowid, content, tags),
    )
    await db.commit()
    return cursor.lastrowid


async def update(memory_id: int, content: str | None = None, tags: str | None = None, relevance_score: float | None = None) -> None:
    db = await get_db()
    updates = {}
    if content is not None:
        updates["content"] = content
    if tags is not None:
        updates["tags"] = tags
    if relevance_score is not None:
        updates["relevance_score"] = relevance_score
    if not updates:
        return
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values())
    await db.execute(f"UPDATE memories SET {set_clause} WHERE id = ?", (*values, memory_id))
    # Update FTS
    if content is not None or tags is not None:
        row = await (await db.execute("SELECT content, tags FROM memories WHERE id = ?", (memory_id,))).fetchone()
        if row:
            await db.execute("DELETE FROM memories_fts WHERE rowid = ?", (memory_id,))
            await db.execute(
                "INSERT INTO memories_fts(rowid, content, tags) VALUES (?, ?, ?)",
                (memory_id, row["content"], row["tags"]),
            )
    await db.commit()


async def delete(memory_id: int) -> None:
    db = await get_db()
    await db.execute("DELETE FROM memories_fts WHERE rowid = ?", (memory_id,))
    await db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    await db.commit()
