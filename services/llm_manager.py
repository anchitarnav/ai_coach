"""LLM provider detection, model listing, and key validation."""

import os
from dataclasses import dataclass, field

PROVIDERS: dict[str, dict] = {
    "anthropic": {
        "env_var": "ANTHROPIC_API_KEY",
        "models": [
            "anthropic:claude-sonnet-4-5",
            "anthropic:claude-haiku-4-5-20251001",
            "anthropic:claude-opus-4-6",
        ],
        "display_name": "Anthropic",
    },
    "openai": {
        "env_var": "OPENAI_API_KEY",
        "models": [
            "openai:gpt-4o",
            "openai:gpt-4o-mini",
            "openai:o3-mini",
        ],
        "display_name": "OpenAI",
    },
    "google": {
        "env_var": "GOOGLE_API_KEY",
        "models": [
            "google-gla:gemini-2.0-flash",
            "google-gla:gemini-2.5-pro-preview-06-05",
        ],
        "display_name": "Google Gemini",
    },
}

def get_default_model() -> str:
    """Return the first available model, preferring the order: Anthropic, OpenAI, Google."""
    models = get_available_models()
    return models[0] if models else "openai:gpt-4o"


@dataclass
class ProviderStatus:
    name: str
    display_name: str
    available: bool
    models: list[str] = field(default_factory=list)


def detect_providers() -> list[ProviderStatus]:
    """Scan environment for available LLM providers."""
    results = []
    for key, info in PROVIDERS.items():
        has_key = bool(os.environ.get(info["env_var"]))
        results.append(
            ProviderStatus(
                name=key,
                display_name=info["display_name"],
                available=has_key,
                models=info["models"] if has_key else [],
            )
        )
    return results


def get_available_models() -> list[str]:
    """Return all model strings for providers that have API keys configured."""
    models = []
    for provider in detect_providers():
        if provider.available:
            models.extend(provider.models)
    return models


def set_api_key(provider_name: str, api_key: str) -> None:
    """Set an API key in the environment for the current process."""
    info = PROVIDERS.get(provider_name)
    if info:
        os.environ[info["env_var"]] = api_key


def get_provider_for_model(model_string: str) -> str | None:
    """Extract provider name from a model string like 'anthropic:claude-sonnet-4-5'."""
    if ":" not in model_string:
        return None
    prefix = model_string.split(":")[0]
    mapping = {"anthropic": "anthropic", "openai": "openai", "google-gla": "google"}
    return mapping.get(prefix)


async def validate_model(model_string: str) -> bool:
    """Quick validation that a model string is usable. Returns True if the provider key exists."""
    provider = get_provider_for_model(model_string)
    if provider is None:
        return False
    info = PROVIDERS.get(provider)
    if info is None:
        return False
    return bool(os.environ.get(info["env_var"]))
