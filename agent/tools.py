"""Agent tools — functions the coaching agent can call to access data."""

from datetime import date
from pydantic_ai import RunContext
from storage import goals as goals_db
from storage import memory as memory_db
from storage import diary as diary_db
from storage import notes as notes_db
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


async def update_commitment_status(ctx: RunContext[None], commitment_id: int, status: str) -> str:
    """Mark a commitment as done, missed, or cancelled.

    Args:
        commitment_id: The numeric ID of the commitment to update.
        status: New status — one of "done", "missed", or "cancelled".
    """
    if status == "done":
        await commitments_db.complete(commitment_id)
        return f"Commitment #{commitment_id} marked as done."
    elif status == "missed":
        await commitments_db.miss(commitment_id)
        return f"Commitment #{commitment_id} marked as missed."
    elif status == "cancelled":
        await commitments_db.cancel(commitment_id)
        return f"Commitment #{commitment_id} marked as cancelled."
    else:
        return f"Invalid status '{status}'. Use 'done', 'missed', or 'cancelled'."


async def search_notes(ctx: RunContext[None], query: str) -> list[dict]:
    """Search the user's reference notes for relevant documents, guidelines, and saved content.

    Notes are persistent reference documents the user has saved — things like HR policies,
    manager expectations, meeting frameworks, or any content they want the coach to reference.

    Args:
        query: Search query to find relevant notes.
    """
    return await notes_db.search(query, limit=10)


async def get_note_by_id(ctx: RunContext[None], note_id: int) -> dict | None:
    """Retrieve a specific note by its ID number. Users may reference notes by ID like 'note #3'.

    Args:
        note_id: The numeric ID of the note to retrieve.
    """
    return await notes_db.get_by_id(note_id)


async def schedule_followup(ctx: RunContext[None], context: str, wake_at: str) -> str:
    """Schedule a follow-up check-in at a future time.

    Args:
        context: What to follow up about (e.g., "Check how the 1:1 with manager went").
        wake_at: ISO timestamp for when to follow up (e.g., "2026-03-01T09:00:00").
    """
    await tasks_db.create(wake_at=wake_at, context=context, source="conversation_scheduled")
    return f"Follow-up scheduled for {wake_at}: {context}"
