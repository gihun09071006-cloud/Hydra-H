"""Provider factory for HYDRA.

Creates AI providers by name::

    provider = ProviderFactory.create("claude")

Adding a future provider (openai, gemini, deepseek, grok) requires only writing a
new provider class and registering it — no change to callers::

    ProviderFactory.register("openai", OpenAIProvider)
"""

from __future__ import annotations

from typing import Type

from providers.base.provider import AIProvider
from providers.claude.claude_provider import ClaudeProvider


class ProviderFactory:
    """Registry-backed factory for :class:`AIProvider` implementations."""

    _providers: dict[str, Type[AIProvider]] = {
        "claude": ClaudeProvider,
    }

    @classmethod
    def create(cls, name: str) -> AIProvider:
        """Return a new provider instance for ``name``.

        Raises :class:`ValueError` for an unknown or invalid provider name.
        """
        if not isinstance(name, str):
            raise ValueError(f"Unknown provider: {name!r}")
        key = name.lower()
        if key not in cls._providers:
            raise ValueError(
                f"Unknown provider: {name!r}. Available: {', '.join(cls.available())}"
            )
        return cls._providers[key]()

    @classmethod
    def register(cls, name: str, provider_cls: Type[AIProvider]) -> None:
        """Register a new provider class under ``name``."""
        if not (isinstance(provider_cls, type) and issubclass(provider_cls, AIProvider)):
            raise TypeError("provider_cls must be an AIProvider subclass")
        cls._providers[name.lower()] = provider_cls

    @classmethod
    def available(cls) -> list[str]:
        """Return the sorted list of registered provider names."""
        return sorted(cls._providers)
