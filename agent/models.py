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


class CommitmentItem(BaseModel):
    what: str = Field(description="What the user committed to doing")
    due_date: str | None = Field(default=None, description="Due date in YYYY-MM-DD format, if mentioned")


class FollowUpItem(BaseModel):
    context: str = Field(description="What the coach should follow up about")
    wake_at: str = Field(description="ISO timestamp for when to follow up")


class DiaryProcessing(BaseModel):
    title: str = Field(description="Short descriptive title for the diary entry (5-8 words)")
    memories: list[MemoryItem] = Field(
        default_factory=list, description="Important memories worth saving from this entry"
    )
    commitments: list[CommitmentItem] = Field(
        default_factory=list, description="Things the user said they'd do"
    )
    follow_ups: list[FollowUpItem] = Field(
        default_factory=list, description="Things the coach should proactively check back on"
    )


class ProactiveDecision(BaseModel):
    nudges: list[NudgeAction] = Field(default_factory=list)
    schedule: list[ScheduledTask] = Field(default_factory=list)
    discard_task_ids: list[int] = Field(default_factory=list)
