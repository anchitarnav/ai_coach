"""Proactive coaching agent — decides when/how to nudge the user."""

from pydantic_ai import Agent

from agent.prompts import PROACTIVE_SYSTEM_PROMPT
from agent.models import ProactiveDecision
from services.llm_manager import get_default_model


def create_proactive_agent(model: str | None = None) -> Agent[None, ProactiveDecision]:
    """Create the proactive agent that outputs structured nudge/schedule decisions."""
    return Agent(
        model or get_default_model(),
        system_prompt=PROACTIVE_SYSTEM_PROMPT,
        output_type=ProactiveDecision,
    )
