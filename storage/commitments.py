"""CRUD operations for user commitments tracked by the coach."""

from storage.database import get_db


async def get_pending() -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        """SELECT * FROM commitments
           WHERE status = 'pending'
           ORDER BY
             CASE WHEN due_date IS NULL THEN 1 ELSE 0 END,
             due_date ASC"""
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_all(limit: int = 50) -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM commitments ORDER BY created_at DESC LIMIT ?", (limit,)
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def create(what: str, due_date: str | None = None, conversation_id: int | None = None) -> int:
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO commitments (what, due_date, conversation_id) VALUES (?, ?, ?)",
        (what, due_date, conversation_id),
    )
    await db.commit()
    return cursor.lastrowid


async def complete(commitment_id: int) -> None:
    db = await get_db()
    await db.execute(
        "UPDATE commitments SET status = 'done', completed_at = CURRENT_TIMESTAMP WHERE id = ?",
        (commitment_id,),
    )
    await db.commit()


async def miss(commitment_id: int) -> None:
    db = await get_db()
    await db.execute(
        "UPDATE commitments SET status = 'missed' WHERE id = ?",
        (commitment_id,),
    )
    await db.commit()


async def cancel(commitment_id: int) -> None:
    db = await get_db()
    await db.execute(
        "UPDATE commitments SET status = 'cancelled' WHERE id = ?",
        (commitment_id,),
    )
    await db.commit()


async def get_overdue() -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM commitments WHERE status = 'pending' AND due_date < date('now') ORDER BY due_date ASC"
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]
