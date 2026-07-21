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
        self._source_url: Optional[str] = None

    def run(self, url: str) -> RenderPrompt:
        """Execute the pipeline for ``url`` (fetch mode) and return a RenderPrompt."""
        if not isinstance(url, str) or not url.strip():
            raise ValueError("url must be a non-empty string")

        # Detect URL type and let the Adapter fetch the raw source. The Adapter
        # is responsible for following redirects for affiliate links; the
        # pipeline never manually parses/rewrites the URL.
        self._adapter.is_affiliate_url(url)  # detection is delegated to the Adapter
        html = self._adapter.fetch(url)
        return self._run_from_html(html)

    def run_from_html(self, html: str, source_url: str) -> RenderPrompt:
        """Execute the pipeline from locally saved HTML and return a RenderPrompt.

        Use when direct HTTP fetching is blocked. The HTML must come from a page
        the user opened normally in their own browser; this method performs no
        network access and no anti-bot bypass. ``source_url`` is validated as a
        Coupang affiliate/product URL and preserved as source metadata.
        """
        # 1. Validate the source URL (recorded as metadata; not fetched).
        self._adapter.validate_source_url(source_url)
        self._source_url = source_url
        # 2. Reject empty HTML.
        if not isinstance(html, str) or not html.strip():
            raise ValueError("html must be a non-empty string")
        # 3-5. Same parser + engine chain as URL mode.
        return self._run_from_html(html)

    def run_from_product_facts(self, product_facts: ProductFacts) -> RenderPrompt:
        """Execute the pipeline from a ProductFacts contract and return a RenderPrompt.

        Used by facts-file mode (extension-captured JSON). Performs no network
        access. Runs the same engine chain as URL and local-HTML modes.
        """
        if not isinstance(product_facts, ProductFacts):
            raise TypeError("product_facts must be a ProductFacts instance")
        return self._run_from_facts(product_facts)

    def _run_from_html(self, html: str) -> RenderPrompt:
        """Parse raw HTML into ProductFacts, then run the shared engine chain."""
        facts = ProductFacts.from_dict(self._parser.extract(html))
        return self._run_from_facts(facts)

    def _run_from_facts(self, facts: ProductFacts) -> RenderPrompt:
        """Shared engine sequencing for every input mode (no duplication)."""
        product_intelligence = self._intelligence.analyze(facts)
        market_fit = self._market_fit.evaluate(product_intelligence.to_dict())
        strategy = self._strategy.decide(product_intelligence, market_fit)
        storyboard = self._story.generate(strategy)
        return self._compiler.compile(storyboard)
