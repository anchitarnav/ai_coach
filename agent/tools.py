"""Agent tools — functions the coaching agent can call to access data."""

from datetime import date
from pydantic_ai import RunContext
from storage import goals as goals_db
from storage import memory as memory_db
from storage import diary as diary_db
from storage import commitments as commitments_db
from storage import scheduled_tasks as tasks_db


async def get_active_goals(ctx: RunContext[None]) -> list[dict]:
    """Retrieve the user's current active career goals with their titles, descriptions, categories, and priorities."""
    return await goals_db.get_active()


async def search_memories(ctx: RunContext[None], query: str) -> list[dict]:
    """Search the user's permanent memory for relevant past context, insights, and decisions.

    Args:
        query: Search query to find relevant memories.
    """
    return await memory_db.search(query, limit=15)


async def get_recent_memories(ctx: RunContext[None], days: int = 14) -> list[dict]:
    """Get recent memories from the last N days.

    Args:
        days: Number of days to look back. Defaults to 14.
    """
    return await memory_db.get_recent(days=days)


async def get_recent_diary_entries(ctx: RunContext[None], days: int = 7) -> list[dict]:
    """Get the user's recent diary entries for context on their current state and reflections.

    Args:
        days: Number of days to look back. Defaults to 7.
    """
    return await diary_db.get_recent(days=days)


async def add_memory(ctx: RunContext[None], content: str, tags: str) -> str:
    """Save an important insight, decision, or context to permanent memory for future reference.

    Args:
        content: The memory content to save.
        tags: Comma-separated tags for searchability.
    """
    await memory_db.create(content=content, source="agent_curated", tags=tags)
    return "Memory saved successfully."


async def get_today_info(ctx: RunContext[None]) -> dict:
    """Get today's date and day of the week for context."""
    today = date.today()
    return {
        "date": today.isoformat(),
        "day_of_week": today.strftime("%A"),
    }


async def create_commitment(ctx: RunContext[None], what: str, due_date: str | None = None) -> str:
    """Track a commitment the user made — something they said they'd do.

    Args:
        what: Description of the commitment (e.g., "Prepare board presentation").
        due_date: Optional due date in YYYY-MM-DD format.
    """
    await commitments_db.create(what=what, due_date=due_date)
    return f"Commitment tracked: {what}" + (f" (due {due_date})" if due_date else "")


async def get_pending_commitments(ctx: RunContext[None]) -> list[dict]:
    """Get the user's pending commitments — things they said they'd do but haven't completed yet."""
    return await commitments_db.get_pending()


async def schedule_followup(ctx: RunContext[None], context: str, wake_at: str) -> str:
    """Schedule a follow-up check-in at a future time.

    Args:
        context: What to follow up about (e.g., "Check how the 1:1 with manager went").
        wake_at: ISO timestamp for when to follow up (e.g., "2026-03-01T09:00:00").
    """
    await tasks_db.create(wake_at=wake_at, context=context, source="conversation_scheduled")
    return f"Follow-up scheduled for {wake_at}: {context}"
