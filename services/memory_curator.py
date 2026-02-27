"""Post-conversation memory extraction logic."""

from datetime import datetime, timedelta

from agent.coach import create_memory_extractor
from agent.models import MemoryExtraction
from storage import conversations as conv_db
from storage import memory as memory_db
from storage import scheduled_tasks as tasks_db


async def curate_memories(conversation_id: int, model: str | None = None) -> MemoryExtraction | None:
    """Run memory extraction on a completed conversation.

    Returns the extraction result, or None if the conversation has too few messages.
    """
    messages = await conv_db.get_messages(conversation_id)
    if len(messages) < 2:
        return None

    # Build conversation transcript
    transcript_parts = []
    for msg in messages:
        role = "User" if msg["role"] == "user" else "Coach"
        transcript_parts.append(f"{role}: {msg['content']}")
    transcript = "\n\n".join(transcript_parts)

    extractor = create_memory_extractor(model)
    result = await extractor.run(
        f"Extract important memories from this coaching conversation:\n\n{transcript}"
    )
    extraction = result.output

    # Save extracted memories
    for mem in extraction.memories:
        await memory_db.create(
            content=mem.content,
            source="agent_curated",
            tags=mem.tags,
            relevance_score=mem.relevance_score,
            conversation_id=conversation_id,
        )

    # Schedule a follow-up if the conversation had substantive content
    if extraction.memories:
        wake_at = (datetime.now() + timedelta(days=2)).replace(hour=9, minute=0, second=0, microsecond=0).isoformat()
        await tasks_db.create(
            wake_at=wake_at,
            context=f"Follow up: {extraction.conversation_summary}",
            source="post_conversation",
        )

    return extraction
