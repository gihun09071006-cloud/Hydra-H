"""AI Provider interface for HYDRA.

HYDRA never calls a specific LLM directly from an Engine. Every Engine
communicates only with this provider abstraction, so the underlying model can be
swapped (Claude today; OpenAI, Gemini, DeepSeek, Grok in the future) without
changing any Engine.

This module defines the interface only. Concrete providers live in sibling
packages (e.g. ``providers/claude``).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    """Abstract interface every AI provider must implement.

    The four methods mirror HYDRA's pipeline stages. Each returns a plain dict
    matching the corresponding contract; no Engine ever depends on a concrete
    provider.
    """

    #: Short provider name; concrete providers set this.
    name: str = ""

    @abstractmethod
    def analyze_product(self, product_facts: dict[str, Any]) -> dict[str, Any]:
        """Turn raw product facts into a Product Intelligence object."""
        raise NotImplementedError

    @abstractmethod
    def generate_creative_strategy(
        self,
        product_intelligence: dict[str, Any],
        market_fit_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Turn a Product Intelligence object (and Market Fit result) into a
        Creative Strategy output."""
        raise NotImplementedError

    @abstractmethod
    def generate_story(self, strategy: dict[str, Any]) -> dict[str, Any]:
        """Turn a Creative Strategy output into a storyboard."""
        raise NotImplementedError

    @abstractmethod
    def compile_prompt(self, story: dict[str, Any]) -> dict[str, Any]:
        """Turn a storyboard into a backend prompt payload."""
        raise NotImplementedError
