"""CRUD operations for nudges (proactive coach notifications)."""

from storage.database import get_db


async def get_pending() -> list[dict]:
    """Get actionable nudges: pending/shown, not currently snoozed."""
    db = await get_db()
    cursor = await db.execute(
        """SELECT * FROM nudges
           WHERE status IN ('pending', 'shown')
             AND (snoozed_until IS NULL OR snoozed_until <= datetime('now'))
           ORDER BY
             CASE priority WHEN 'urgent' THEN 0 WHEN 'important' THEN 1 ELSE 2 END,
             created_at ASC"""
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_history(limit: int = 50) -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM nudges ORDER BY created_at DESC LIMIT ?", (limit,)
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def create(message: str, chat_context: str = "", priority: str = "gentle", source_task_id: int | None = None) -> int:
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO nudges (message, chat_context, priority, source_task_id) VALUES (?, ?, ?, ?)",
        (message, chat_context, priority, source_task_id),
    )
    await db.commit()
    return cursor.lastrowid


async def show(nudge_id: int) -> None:
    db = await get_db()
    await db.execute(
        "UPDATE nudges SET status = 'shown', shown_at = CURRENT_TIMESTAMP WHERE id = ?",
        (nudge_id,),
    )
    await db.commit()


async def snooze(nudge_id: int, until: str) -> None:
    db = await get_db()
    await db.execute(
        "UPDATE nudges SET status = 'snoozed', snoozed_until = ? WHERE id = ?",
        (until, nudge_id),
    )
    await db.commit()


async def dismiss(nudge_id: int) -> None:
    db = await get_db()
    await db.execute(
        "UPDATE nudges SET status = 'dismissed' WHERE id = ?",
        (nudge_id,),
    )
    await db.commit()


async def act_on(nudge_id: int, conversation_id: int | None = None) -> None:
    db = await get_db()
    await db.execute(
        "UPDATE nudges SET status = 'acted_on', acted_at = CURRENT_TIMESTAMP, conversation_id = ? WHERE id = ?",
        (conversation_id, nudge_id),
    )
    await db.commit()


async def count_pending() -> int:
    db = await get_db()
    cursor = await db.execute(
        """SELECT COUNT(*) FROM nudges
           WHERE status IN ('pending', 'shown')
             AND (snoozed_until IS NULL OR snoozed_until <= datetime('now'))"""
    )
    row = await cursor.fetchone()
    return row[0]


async def has_similar_pending(fragment: str) -> bool:
    """Check if a nudge with similar text already exists (deduplication)."""
    db = await get_db()
    cursor = await db.execute(
        """SELECT COUNT(*) FROM nudges
           WHERE status IN ('pending', 'shown', 'snoozed')
             AND message LIKE ?""",
        (f"%{fragment}%",),
    )
    row = await cursor.fetchone()
    return row[0] > 0
