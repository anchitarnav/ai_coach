"""CRUD operations for diary entries."""

from datetime import date
from storage.database import get_db


async def get_all(limit: int = 50, offset: int = 0) -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM diary_entries ORDER BY date DESC LIMIT ? OFFSET ?",
        (limit, offset),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_recent(days: int = 7) -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        """SELECT * FROM diary_entries
           WHERE date >= date('now', ?)
           ORDER BY date DESC""",
        (f"-{days} days",),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_by_date(entry_date: date) -> dict | None:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM diary_entries WHERE date = ?",
        (entry_date.isoformat(),),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def get_by_id(entry_id: int) -> dict | None:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM diary_entries WHERE id = ?", (entry_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def create(entry_date: date, content: str, mood: str = "", title: str = "") -> int:
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO diary_entries (date, content, mood, title) VALUES (?, ?, ?, ?)",
        (entry_date.isoformat(), content, mood, title),
    )
    await db.commit()
    return cursor.lastrowid


async def update(entry_id: int, content: str | None = None, mood: str | None = None, title: str | None = None) -> None:
    db = await get_db()
    updates = {}
    if content is not None:
        updates["content"] = content
    if mood is not None:
        updates["mood"] = mood
    if title is not None:
        updates["title"] = title
    if not updates:
        return
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values())
    await db.execute(
        f"UPDATE diary_entries SET {set_clause} WHERE id = ?",
        (*values, entry_id),
    )
    await db.commit()


async def delete(entry_id: int) -> None:
    db = await get_db()
    await db.execute("DELETE FROM diary_entries WHERE id = ?", (entry_id,))
    await db.commit()
