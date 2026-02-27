"""Pydantic models for structured agent outputs."""

from pydantic import BaseModel, Field


class MemoryItem(BaseModel):
    content: str = Field(description="The memory content to save")
    tags: str = Field(description="Comma-separated tags for searchability")
    relevance_score: float = Field(
        ge=0.0, le=1.0, description="Importance score from 0 to 1"
    )


class MemoryExtraction(BaseModel):
    memories: list[MemoryItem] = Field(
        default_factory=list, description="Memories to extract and save"
    )
    conversation_summary: str = Field(
        description="Brief summary of the conversation"
    )


class NudgeAction(BaseModel):
    message: str = Field(description="The nudge message to show the user")
    chat_context: str = Field(default="", description="Context to pre-load if user clicks 'Let's talk'")
    priority: str = Field(default="gentle", description="gentle | important | urgent")


class ScheduledTask(BaseModel):
    wake_at: str = Field(description="ISO timestamp, e.g. '2026-02-28T09:00:00'")
    context: str = Field(description="What to check on at wake time")
    source: str = Field(default="agent_scheduled")
    related_goal_id: int | None = Field(default=None)


class ProactiveDecision(BaseModel):
    nudges: list[NudgeAction] = Field(default_factory=list)
    schedule: list[ScheduledTask] = Field(default_factory=list)
    discard_task_ids: list[int] = Field(default_factory=list)
