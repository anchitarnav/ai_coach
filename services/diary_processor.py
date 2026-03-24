"""Post-save diary entry processing: title generation, memory extraction, commitments, follow-ups."""

from agent.coach import create_diary_processor
from agent.models import DiaryProcessing
from storage import diary as diary_db
from storage import memory as memory_db
from storage import settings as settings_db
from storage import scheduled_tasks as tasks_db
from storage import commitments as commitments_db


async def process_diary_entry(entry_id: int) -> DiaryProcessing | None:
    """Run AI processing on a diary entry. Returns the result or None on failure."""
    entry = await diary_db.get_by_id(entry_id)
    if not entry:
        return None

    model = await settings_db.get("default_model")
    processor = create_diary_processor(model)

    prompt = (
        f"Process this diary entry:\n\n"
        f"Date: {entry['date']}\n"
        f"Mood: {entry['mood'] or 'not specified'}\n\n"
        f"{entry['content']}"
    )
    result = await processor.run(prompt)
    processing = result.output

    # Save the AI-generated title
    await diary_db.update(entry_id, title=processing.title)

    # Save extracted memories
    for mem in processing.memories:
        await memory_db.create(
            content=mem.content,
            source="diary_derived",
            tags=mem.tags,
            relevance_score=mem.relevance_score,
        )

    # Track commitments
    for commit in processing.commitments:
        await commitments_db.create(what=commit.what, due_date=commit.due_date)

    # Schedule follow-ups
    for followup in processing.follow_ups:
        await tasks_db.create(
            wake_at=followup.wake_at,
            context=followup.context,
            source="diary_processing",
        )

    return processing
