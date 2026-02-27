"""CRUD operations for scheduled tasks (proactive coach wake-ups)."""

from datetime import datetime

from storage.database import get_db


async def get_pending(before_time: str | None = None) -> list[dict]:
    """Get pending tasks whose wake_at has passed (or is before `before_time`)."""
    db = await get_db()
    # Use local time with consistent ISO format (T separator) to match stored values
    now = before_time or datetime.now().isoformat()
    cursor = await db.execute(
        "SELECT * FROM scheduled_tasks WHERE status = 'pending' AND REPLACE(wake_at, 'T', ' ') <= REPLACE(?, 'T', ' ') ORDER BY wake_at ASC",
        (now,),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def create(wake_at: str, context: str, source: str = "heartbeat", related_goal_id: int | None = None) -> int:
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO scheduled_tasks (wake_at, context, source, related_goal_id) VALUES (?, ?, ?, ?)",
        (wake_at, context, source, related_goal_id),
    )
    await db.commit()
    return cursor.lastrowid


async def update_status(task_id: int, status: str) -> None:
    db = await get_db()
    if status == "fired":
        await db.execute(
            "UPDATE scheduled_tasks SET status = ?, fired_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, task_id),
        )
    else:
        await db.execute(
            "UPDATE scheduled_tasks SET status = ? WHERE id = ?",
            (status, task_id),
        )
    await db.commit()


async def cancel(task_id: int) -> None:
    await update_status(task_id, "cancelled")
