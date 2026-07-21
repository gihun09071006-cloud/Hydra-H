"""Provider factory for HYDRA.

Creates AI providers by name::

    provider = ProviderFactory.create("claude")

For ``claude``, selection is driven by ``HYDRA_AI_MODE`` (default ``mock``):

    HYDRA_AI_MODE=mock  -> MockClaudeProvider (deterministic, offline)
    HYDRA_AI_MODE=live  -> ClaudeProvider (real Anthropic API; requires ANTHROPIC_API_KEY)

There is no silent fallback from live to mock.

Adding a future provider requires only writing a new provider class and
registering it::

    ProviderFactory.register("openai", OpenAIProvider)
"""

from __future__ import annotations

import os
from typing import Type

from providers.base.provider import AIProvider
from providers.claude.claude_provider import ClaudeProvider
from providers.claude.mock_claude_provider import MockClaudeProvider

_ALLOWED_AI_MODES = ("mock", "live")


class ProviderFactory:
    """Registry-backed factory for :class:`AIProvider` implementations."""

    _providers: dict[str, Type[AIProvider]] = {
        "claude": ClaudeProvider,
    }

    @classmethod
    def create(cls, name: str) -> AIProvider:
        """Return a new provider instance for ``name``.

        Raises :class:`ValueError` for an unknown/invalid name, an invalid
        ``HYDRA_AI_MODE``, or live mode without an API key.
        """
        if not isinstance(name, str):
            raise ValueError(f"Unknown provider: {name!r}")
        key = name.lower()
        if key not in cls._providers:
            raise ValueError(
                f"Unknown provider: {name!r}. Available: {', '.join(cls.available())}"
            )

        if key == "claude":
            return cls._create_claude()
        return cls._providers[key]()

    @classmethod
    def _create_claude(cls) -> AIProvider:
        mode = os.environ.get("HYDRA_AI_MODE", "mock").strip().lower()
        if mode == "mock":
            return MockClaudeProvider()
        if mode == "live":
            if not os.environ.get("ANTHROPIC_API_KEY"):
                raise ValueError("ANTHROPIC_API_KEY is required for HYDRA_AI_MODE=live")
            return ClaudeProvider()
        raise ValueError(
            f"invalid HYDRA_AI_MODE: {mode!r} (allowed: {', '.join(_ALLOWED_AI_MODES)})"
        )

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
