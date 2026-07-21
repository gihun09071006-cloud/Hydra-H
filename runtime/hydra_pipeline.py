"""HYDRA runtime pipeline orchestrator.

Application entry point. Given a Coupang URL (affiliate link or direct product
URL), it runs the complete HYDRA pipeline and returns a :class:`RenderPrompt`:

    Adapter -> Parser -> ProductFacts -> Product Intelligence Engine
            -> Market Fit Engine -> Creative Strategy Engine
            -> Story Engine -> Prompt Compiler Engine -> RenderPrompt

This module is orchestration only. It contains no AI, business, marketing,
prompt-engineering, or story-generation logic — every stage is delegated to the
existing components. Any invalid URL, invalid intermediate contract, or engine
failure stops execution immediately and propagates.
"""

from __future__ import annotations

from typing import Optional

from adapters.coupang.coupang_adapter import CoupangAdapter
from contracts.product_facts import ProductFacts
from contracts.render_prompt import RenderPrompt
from engines.creative_strategy_engine import CreativeStrategyEngine
from engines.market_fit_engine import MarketFitEngine
from engines.product_intelligence_engine import ProductIntelligenceEngine
from engines.prompt_compiler_engine import PromptCompilerEngine
from engines.story_engine import StoryEngine
from parsers.product_parser import ProductParser
from providers.base.provider import AIProvider
from providers.claude.claude_provider import ClaudeProvider


class HydraPipeline:
    """Runs the full HYDRA pipeline for a Coupang URL."""

    def __init__(
        self,
        provider: Optional[AIProvider] = None,
        adapter: Optional[CoupangAdapter] = None,
    ) -> None:
        provider = provider or ClaudeProvider()
        if not isinstance(provider, AIProvider):
            raise TypeError("provider must be an AIProvider instance")

        self._adapter = adapter or CoupangAdapter()
        self._parser = ProductParser()
        self._intelligence = ProductIntelligenceEngine(provider)
        self._market_fit = MarketFitEngine()
        self._strategy = CreativeStrategyEngine(provider)
        self._story = StoryEngine(provider)
        self._compiler = PromptCompilerEngine(provider)

    def run(self, url: str) -> RenderPrompt:
        """Execute the pipeline for ``url`` and return a RenderPrompt."""
        if not isinstance(url, str) or not url.strip():
            raise ValueError("url must be a non-empty string")

        # 1. Detect URL type and let the Adapter fetch the raw source. The
        #    Adapter is responsible for following redirects for affiliate links;
        #    the pipeline never manually parses/rewrites the URL.
        self._adapter.is_affiliate_url(url)  # detection is delegated to the Adapter
        html = self._adapter.fetch(url)

        # 2. Run the pipeline stages in order.
        facts = ProductFacts.from_dict(self._parser.extract(html))
        product_intelligence = self._intelligence.analyze(facts)
        market_fit = self._market_fit.evaluate(product_intelligence.to_dict())
        strategy = self._strategy.decide(product_intelligence, market_fit)
        storyboard = self._story.generate(strategy)
        render_prompt = self._compiler.compile(storyboard)

        # 3. Return the RenderPrompt.
        return render_prompt
