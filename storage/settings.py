"""Key-value settings storage."""

import json
from storage.database import get_db


async def get(key: str, default: str | None = None) -> str | None:
    db = await get_db()
    cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = await cursor.fetchone()
    return row["value"] if row else default


async def get_json(key: str, default=None):
    raw = await get(key)
    if raw is None:
        return default
    return json.loads(raw)


async def set(key: str, value: str) -> None:
    db = await get_db()
    await db.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = ?",
        (key, value, value),
    )
    await db.commit()


async def set_json(key: str, value) -> None:
    await set(key, json.dumps(value))


async def delete(key: str) -> None:
    db = await get_db()
    await db.execute("DELETE FROM settings WHERE key = ?", (key,))
    await db.commit()


async def get_all() -> dict[str, str]:
    db = await get_db()
    cursor = await db.execute("SELECT key, value FROM settings")
    rows = await cursor.fetchall()
    return {r["key"]: r["value"] for r in rows}
