"""Prompt Compiler Engine for HYDRA.

Orchestration only. The engine receives a :class:`Storyboard` contract, delegates
prompt compilation to the configured AI Provider, validates the returned
:class:`RenderPrompt` contract, and returns it.

The engine contains no prompt-engineering logic, rendering logic,
Higgsfield-specific logic, business rules, or networking. All compilation is
delegated to the provider abstraction.
"""

from __future__ import annotations

from typing import Any

from contracts.render_prompt import RenderPrompt
from contracts.storyboard import Storyboard
from providers.base.provider import AIProvider

# The RenderPrompt keys a provider result must contain.
_REQUIRED_PROMPT_KEYS = ("target_backend", "prompt", "negative_prompt", "metadata")


class PromptCompilerEngine:
    """Turns a Storyboard into a RenderPrompt via an AI Provider."""

    def __init__(self, provider: AIProvider) -> None:
        if not isinstance(provider, AIProvider):
            raise TypeError("provider must be an AIProvider instance")
        self._provider = provider

    def compile(self, storyboard: Storyboard) -> RenderPrompt:
        """Validate the storyboard, delegate to the provider, return a RenderPrompt."""
        self._validate_storyboard(storyboard)
        raw = self._provider.compile_prompt(storyboard.to_dict())
        return self._validate_prompt(raw)

    @staticmethod
    def _validate_storyboard(storyboard: Storyboard) -> None:
        if not isinstance(storyboard, Storyboard):
            raise TypeError("storyboard must be a Storyboard instance")
        if not storyboard.scenes:
            raise ValueError("Storyboard.scenes must not be empty")

    @staticmethod
    def _validate_prompt(raw: Any) -> RenderPrompt:
        if isinstance(raw, RenderPrompt):
            return raw
        if not isinstance(raw, dict):
            raise TypeError(
                "provider.compile_prompt must return a dict or RenderPrompt"
            )
        missing = [k for k in _REQUIRED_PROMPT_KEYS if k not in raw]
        if missing:
            raise ValueError(
                f"provider returned an incomplete RenderPrompt; missing: {missing}"
            )
        if not isinstance(raw["metadata"], dict):
            raise ValueError("RenderPrompt.metadata must be a dict")
        return RenderPrompt.from_dict(raw)
