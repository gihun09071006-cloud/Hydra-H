"""Creative Strategy Engine for HYDRA.

Orchestration only. The engine receives a :class:`ProductIntelligence` contract
and a Market Fit result, delegates the creative decision to the configured AI
Provider, validates the returned :class:`CreativeStrategy` contract, and returns
it.

The engine contains no prompt text, marketing/strategy logic, scoring, business
rules, hardcoded strategies, or networking. All decision-making is delegated to
the provider abstraction.
"""

from __future__ import annotations

from typing import Any

from contracts.creative_strategy import CreativeStrategy
from contracts.product_intelligence import ProductIntelligence
from providers.base.provider import AIProvider

# The Market Fit result keys the engine requires to be present.
_REQUIRED_MARKET_FIT_KEYS = ("market_fit_score", "decision")

# The CreativeStrategy keys a provider result must contain.
_REQUIRED_STRATEGY_KEYS = (
    "strategy",
    "reason",
    "confidence",
    "hook_type",
    "story_pattern",
    "cta_style",
)


class CreativeStrategyEngine:
    """Turns ProductIntelligence + Market Fit into a CreativeStrategy via a Provider."""

    def __init__(self, provider: AIProvider) -> None:
        if not isinstance(provider, AIProvider):
            raise TypeError("provider must be an AIProvider instance")
        self._provider = provider

    def decide(
        self,
        product_intelligence: ProductIntelligence,
        market_fit_result: dict[str, Any],
    ) -> CreativeStrategy:
        """Validate inputs, delegate to the provider, return a CreativeStrategy."""
        self._validate_product_intelligence(product_intelligence)
        self._validate_market_fit(market_fit_result)
        raw = self._provider.generate_creative_strategy(
            product_intelligence.to_dict(), market_fit_result
        )
        return self._validate_strategy(raw)

    @staticmethod
    def _validate_product_intelligence(pi: ProductIntelligence) -> None:
        if not isinstance(pi, ProductIntelligence):
            raise TypeError("product_intelligence must be a ProductIntelligence instance")
        if not pi.product_identity.product_name or not str(
            pi.product_identity.product_name
        ).strip():
            raise ValueError("ProductIntelligence.product_identity.product_name is required")

    @staticmethod
    def _validate_market_fit(market_fit_result: dict[str, Any]) -> None:
        if not isinstance(market_fit_result, dict):
            raise TypeError("market_fit_result must be a dict")
        missing = [k for k in _REQUIRED_MARKET_FIT_KEYS if k not in market_fit_result]
        if missing:
            raise ValueError(f"market_fit_result is missing keys: {missing}")

    @staticmethod
    def _validate_strategy(raw: Any) -> CreativeStrategy:
        if isinstance(raw, CreativeStrategy):
            return raw
        if not isinstance(raw, dict):
            raise TypeError(
                "provider.generate_creative_strategy must return a dict or CreativeStrategy"
            )
        missing = [k for k in _REQUIRED_STRATEGY_KEYS if k not in raw]
        if missing:
            raise ValueError(
                f"provider returned an incomplete CreativeStrategy; missing: {missing}"
            )
        return CreativeStrategy.from_dict(raw)
