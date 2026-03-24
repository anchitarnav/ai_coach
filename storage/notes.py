"""CRUD operations for reference notes."""

from datetime import datetime

from storage.database import get_db


async def get_all(limit: int = 100, offset: int = 0) -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM notes ORDER BY updated_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_by_id(note_id: int) -> dict | None:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def search(query: str, limit: int = 20) -> list[dict]:
    db = await get_db()
    # Quote the query so FTS5 treats it as literal tokens, not column references
    safe_query = '"' + query.replace('"', '""') + '"'
    cursor = await db.execute(
        """SELECT n.*, rank
           FROM notes_fts fts
           JOIN notes n ON n.id = fts.rowid
           WHERE notes_fts MATCH ?
           ORDER BY rank
           LIMIT ?""",
        (safe_query, limit),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def create(title: str, content: str = "", tags: str = "") -> int:
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO notes (title, content, tags) VALUES (?, ?, ?)",
        (title, content, tags),
    )
    await db.execute(
        "INSERT INTO notes_fts(rowid, title, content, tags) VALUES (?, ?, ?, ?)",
        (cursor.lastrowid, title, content, tags),
    )
    await db.commit()
    return cursor.lastrowid


async def update(note_id: int, title: str | None = None, content: str | None = None, tags: str | None = None) -> None:
    db = await get_db()
    updates = {}
    if title is not None:
        updates["title"] = title
    if content is not None:
        updates["content"] = content
    if tags is not None:
        updates["tags"] = tags
    if not updates:
        return
    updates["updated_at"] = datetime.now().isoformat()
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values())
    await db.execute(f"UPDATE notes SET {set_clause} WHERE id = ?", (*values, note_id))
    # Rebuild FTS for this row
    if title is not None or content is not None or tags is not None:
        row = await (await db.execute("SELECT title, content, tags FROM notes WHERE id = ?", (note_id,))).fetchone()
        if row:
            await db.execute("DELETE FROM notes_fts WHERE rowid = ?", (note_id,))
            await db.execute(
                "INSERT INTO notes_fts(rowid, title, content, tags) VALUES (?, ?, ?, ?)",
                (note_id, row["title"], row["content"], row["tags"]),
            )
    await db.commit()


async def delete(note_id: int) -> None:
    db = await get_db()
    await db.execute("DELETE FROM notes_fts WHERE rowid = ?", (note_id,))
    await db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    await db.commit()
