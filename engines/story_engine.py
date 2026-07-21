"""Story Engine for HYDRA.

Orchestration only. The engine receives a :class:`CreativeStrategy` contract,
delegates storyboard generation to the configured AI Provider, validates the
returned :class:`Storyboard` contract, and returns it.

The engine contains no prompt text, storytelling logic, scene-generation logic,
business rules, or networking. All generation is delegated to the provider
abstraction.
"""

from __future__ import annotations

from typing import Any

from contracts.creative_strategy import CreativeStrategy
from contracts.storyboard import Storyboard
from providers.base.provider import AIProvider

# The Storyboard keys a provider result must contain.
_REQUIRED_STORYBOARD_KEYS = ("story_pattern", "duration", "scenes")


class StoryEngine:
    """Turns a CreativeStrategy into a Storyboard via an AI Provider."""

    def __init__(self, provider: AIProvider) -> None:
        if not isinstance(provider, AIProvider):
            raise TypeError("provider must be an AIProvider instance")
        self._provider = provider

    def generate(self, creative_strategy: CreativeStrategy) -> Storyboard:
        """Validate the strategy, delegate to the provider, return a Storyboard."""
        self._validate_strategy(creative_strategy)
        raw = self._provider.generate_story(creative_strategy.to_dict())
        return self._validate_storyboard(raw)

    @staticmethod
    def _validate_strategy(creative_strategy: CreativeStrategy) -> None:
        if not isinstance(creative_strategy, CreativeStrategy):
            raise TypeError("creative_strategy must be a CreativeStrategy instance")
        if not creative_strategy.strategy or not str(creative_strategy.strategy).strip():
            raise ValueError("CreativeStrategy.strategy is required")

    @staticmethod
    def _validate_storyboard(raw: Any) -> Storyboard:
        if isinstance(raw, Storyboard):
            return raw
        if not isinstance(raw, dict):
            raise TypeError(
                "provider.generate_story must return a dict or Storyboard"
            )
        missing = [k for k in _REQUIRED_STORYBOARD_KEYS if k not in raw]
        if missing:
            raise ValueError(
                f"provider returned an incomplete Storyboard; missing: {missing}"
            )
        if not isinstance(raw["scenes"], list):
            raise ValueError("Storyboard.scenes must be a list")
        return Storyboard.from_dict(raw)
