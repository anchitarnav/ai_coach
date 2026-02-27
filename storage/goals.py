"""CRUD operations for career goals."""

from storage.database import get_db


async def get_active() -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM goals WHERE is_active = 1 ORDER BY priority ASC, created_at DESC"
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_all() -> list[dict]:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM goals ORDER BY is_active DESC, priority ASC")
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_by_id(goal_id: int) -> dict | None:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def create(title: str, description: str = "", category: str = "", priority: int = 3) -> int:
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO goals (title, description, category, priority) VALUES (?, ?, ?, ?)",
        (title, description, category, priority),
    )
    await db.commit()
    return cursor.lastrowid


async def update(goal_id: int, **fields) -> None:
    if not fields:
        return
    allowed = {"title", "description", "category", "priority", "is_active"}
    filtered = {k: v for k, v in fields.items() if k in allowed}
    if not filtered:
        return
    filtered["updated_at"] = "CURRENT_TIMESTAMP"
    set_clause = ", ".join(
        f"{k} = CURRENT_TIMESTAMP" if k == "updated_at" else f"{k} = ?"
        for k in filtered
    )
    values = [v for k, v in filtered.items() if k != "updated_at"]
    db = await get_db()
    await db.execute(
        f"UPDATE goals SET {set_clause} WHERE id = ?",
        (*values, goal_id),
    )
    await db.commit()


async def delete(goal_id: int) -> None:
    db = await get_db()
    await db.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
    await db.commit()
