"""Product Intelligence Engine for HYDRA.

Orchestration only. The engine receives a :class:`ProductFacts` contract, calls
the configured AI Provider to analyze it, validates the result as a
:class:`ProductIntelligence` contract, and returns it.

The engine contains no prompt, no product analysis, no scoring, and no
networking. All analysis is delegated to the provider abstraction.
"""

from __future__ import annotations

from typing import Any

from contracts.product_facts import ProductFacts
from contracts.product_intelligence import ProductIntelligence
from providers.base.provider import AIProvider

# The top-level sections a ProductIntelligence contract must contain.
_REQUIRED_SECTIONS = (
    "product_identity",
    "functional_analysis",
    "visual_analysis",
    "customer_analysis",
    "pain_analysis",
    "objection_analysis",
    "competitive_analysis",
    "virality_analysis",
    "platform_recommendation",
)


class ProductIntelligenceEngine:
    """Turns ProductFacts into ProductIntelligence via an AI Provider."""

    def __init__(self, provider: AIProvider) -> None:
        if not isinstance(provider, AIProvider):
            raise TypeError("provider must be an AIProvider instance")
        self._provider = provider

    def analyze(self, facts: ProductFacts) -> ProductIntelligence:
        """Validate ``facts``, delegate to the provider, return ProductIntelligence."""
        self._validate_facts(facts)
        raw = self._provider.analyze_product(facts.to_dict())
        return self._validate_intelligence(raw)

    @staticmethod
    def _validate_facts(facts: ProductFacts) -> None:
        if not isinstance(facts, ProductFacts):
            raise TypeError("facts must be a ProductFacts instance")
        if not facts.product_name or not str(facts.product_name).strip():
            raise ValueError("ProductFacts.product_name is required")

    @staticmethod
    def _validate_intelligence(raw: Any) -> ProductIntelligence:
        if isinstance(raw, ProductIntelligence):
            return raw
        if not isinstance(raw, dict):
            raise TypeError(
                "provider.analyze_product must return a dict or ProductIntelligence"
            )
        missing = [key for key in _REQUIRED_SECTIONS if key not in raw]
        if missing:
            raise ValueError(
                f"provider returned an incomplete ProductIntelligence; missing: {missing}"
            )
        return ProductIntelligence.from_dict(raw)
