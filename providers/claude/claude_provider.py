"""Real Anthropic-backed Claude provider.

Implements the :class:`AIProvider` interface with the Anthropic Messages API.
Each method builds a stage-specific prompt, makes exactly one API call, parses
strict JSON through the shared parser, validates the required fields, and returns
the existing contract object.

Configuration comes from the environment:
    ANTHROPIC_API_KEY  — required to run live (never logged or stored on the instance)
    ANTHROPIC_MODEL    — optional model override

No retries, no streaming, no tools, no web search in this provider.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from contracts.creative_strategy import CreativeStrategy
from contracts.product_facts import ProductFacts
from contracts.product_intelligence import ProductIntelligence
from contracts.render_prompt import RenderPrompt
from contracts.storyboard import Storyboard
from prompts import (
    CREATIVE_STRATEGY_SYSTEM,
    PRODUCT_INTELLIGENCE_SYSTEM,
    PROMPT_COMPILER_SYSTEM,
    STORY_SYSTEM,
    build_creative_strategy_prompt,
    build_product_intelligence_prompt,
    build_prompt_compiler_prompt,
    build_story_prompt,
)
from providers.base.provider import AIProvider
from providers.json_response_parser import ProviderResponseError, parse_json_response

# Single provider configuration location. Do not scatter model names elsewhere.
DEFAULT_MODEL = "claude-opus-4-8"
DEFAULT_MAX_TOKENS = 4096

_PRODUCT_INTELLIGENCE_KEYS = (
    "product_identity", "functional_analysis", "visual_analysis", "customer_analysis",
    "pain_analysis", "objection_analysis", "competitive_analysis", "virality_analysis",
    "platform_recommendation",
)
_CREATIVE_STRATEGY_KEYS = (
    "strategy", "reason", "confidence", "hook_type", "story_pattern", "cta_style",
)
_STORYBOARD_KEYS = ("story_pattern", "duration", "scenes")
_RENDER_PROMPT_KEYS = ("target_backend", "prompt", "negative_prompt", "metadata")


class ProviderConfigError(RuntimeError):
    """Raised when live provider configuration is missing (e.g. no API key)."""


def _require(data: dict[str, Any], keys: tuple[str, ...]) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        raise ProviderResponseError(f"provider JSON is missing keys: {missing}")


class ClaudeProvider(AIProvider):
    """Anthropic-backed provider. Returns HYDRA contract objects."""

    name = "claude"

    def __init__(self, client: Any = None, model: Optional[str] = None) -> None:
        # An injectable Anthropic client (for tests). The default client is built
        # lazily only when one is not injected.
        self._client = client
        self._model = model or os.environ.get("ANTHROPIC_MODEL") or DEFAULT_MODEL

    # -- AIProvider interface ----------------------------------------------

    def analyze_product(self, product_facts: Any) -> ProductIntelligence:
        facts = product_facts if isinstance(product_facts, ProductFacts) else ProductFacts.from_dict(
            product_facts or {}
        )
        data = self._call(PRODUCT_INTELLIGENCE_SYSTEM, build_product_intelligence_prompt(facts))
        _require(data, _PRODUCT_INTELLIGENCE_KEYS)
        return ProductIntelligence.from_dict(data)

    def generate_creative_strategy(
        self,
        product_intelligence: Any,
        market_fit_result: Optional[dict[str, Any]] = None,
    ) -> CreativeStrategy:
        pi = product_intelligence if isinstance(product_intelligence, ProductIntelligence) else (
            ProductIntelligence.from_dict(product_intelligence or {})
        )
        data = self._call(
            CREATIVE_STRATEGY_SYSTEM,
            build_creative_strategy_prompt(pi, market_fit_result),
        )
        _require(data, _CREATIVE_STRATEGY_KEYS)
        return CreativeStrategy.from_dict(data)

    def generate_story(self, strategy: Any) -> Storyboard:
        cs = strategy if isinstance(strategy, CreativeStrategy) else CreativeStrategy.from_dict(
            strategy or {}
        )
        data = self._call(STORY_SYSTEM, build_story_prompt(cs))
        _require(data, _STORYBOARD_KEYS)
        return Storyboard.from_dict(data)

    def compile_prompt(self, story: Any) -> RenderPrompt:
        sb = story if isinstance(story, Storyboard) else Storyboard.from_dict(story or {})
        data = self._call(PROMPT_COMPILER_SYSTEM, build_prompt_compiler_prompt(sb))
        _require(data, _RENDER_PROMPT_KEYS)
        return RenderPrompt.from_dict(data)

    # -- Anthropic call ----------------------------------------------------

    def _call(self, system: str, user: str) -> dict[str, Any]:
        """Make exactly one Anthropic Messages API call and parse strict JSON."""
        client = self._client_or_default()
        response = client.messages.create(
            model=self._model,
            max_tokens=DEFAULT_MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return parse_json_response(response)

    def _client_or_default(self) -> Any:
        if self._client is None:
            try:
                import anthropic
            except ImportError as exc:  # pragma: no cover - anthropic optional at import
                raise ProviderConfigError(
                    "the 'anthropic' package is required for live mode"
                ) from exc
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ProviderConfigError("ANTHROPIC_API_KEY is required for live mode")
            # The key is passed to the SDK only; it is never stored on the instance,
            # logged, or serialized.
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client
