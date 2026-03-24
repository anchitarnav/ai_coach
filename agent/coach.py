"""Main coaching agent built with PydanticAI."""

from datetime import date

from pydantic_ai import Agent

from agent.prompts import COACHING_SYSTEM_PROMPT, MEMORY_EXTRACTION_PROMPT, DIARY_PROCESSING_PROMPT
from agent.models import MemoryExtraction, DiaryProcessing
from agent.tools import (
    get_active_goals,
    search_memories,
    get_recent_memories,
    get_recent_diary_entries,
    add_memory,
    get_today_info,
    create_commitment,
    get_pending_commitments,
    update_commitment_status,
    schedule_followup,
    search_notes,
    get_note_by_id,
)
from services.llm_manager import get_default_model


def create_coach_agent(model: str | None = None) -> Agent:
    """Create the coaching agent with the specified model."""
    today = date.today()
    date_context = f"\n\nToday is {today.isoformat()} ({today.strftime('%A')}). Use this for any date-related decisions, scheduling, and follow-ups.\n"
    return Agent(
        model or get_default_model(),
        system_prompt=COACHING_SYSTEM_PROMPT + date_context,
        tools=[
            get_active_goals,
            search_memories,
            get_recent_memories,
            get_recent_diary_entries,
            add_memory,
            get_today_info,
            create_commitment,
            get_pending_commitments,
            update_commitment_status,
            schedule_followup,
            search_notes,
            get_note_by_id,
        ],
    )


def create_diary_processor(model: str | None = None) -> Agent[None, DiaryProcessing]:
    """Create an agent for processing diary entries (title generation + memory extraction)."""
    today = date.today()
    date_context = f"\n\nToday is {today.isoformat()} ({today.strftime('%A')}). Use this for computing follow-up dates.\n"
    return Agent(
        model or get_default_model(),
        system_prompt=DIARY_PROCESSING_PROMPT + date_context,
        output_type=DiaryProcessing,
    )


def create_memory_extractor(model: str | None = None) -> Agent[None, MemoryExtraction]:
    """Create an agent for extracting memories from conversations."""
    return Agent(
        model or get_default_model(),
        system_prompt=MEMORY_EXTRACTION_PROMPT,
        output_type=MemoryExtraction,
    )
