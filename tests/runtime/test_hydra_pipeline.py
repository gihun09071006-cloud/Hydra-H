"""Tests for the HYDRA runtime pipeline orchestrator."""

import socket
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from contracts.render_prompt import RenderPrompt  # noqa: E402
from providers.base.provider import AIProvider  # noqa: E402
from providers.claude.claude_provider import ClaudeProvider  # noqa: E402
from runtime.hydra_pipeline import HydraPipeline  # noqa: E402

AFFILIATE_URL = "https://link.coupang.com/a/abcdef"
DIRECT_URL = "https://www.coupang.com/vp/products/1234567890"


class RecordingProvider(AIProvider):
    """Wraps ClaudeProvider and records the order of provider calls."""

    name = "recording"

    def __init__(self):
        self.calls: list[str] = []
        self.creative_args = None
        self._d = ClaudeProvider()

    def analyze_product(self, product_facts):
        self.calls.append("analyze_product")
        assert isinstance(product_facts, dict)
        return self._d.analyze_product(product_facts)

    def generate_creative_strategy(self, product_intelligence, market_fit_result=None):
        self.calls.append("generate_creative_strategy")
        self.creative_args = (product_intelligence, market_fit_result)
        return self._d.generate_creative_strategy(product_intelligence, market_fit_result)

    def generate_story(self, strategy):
        self.calls.append("generate_story")
        return self._d.generate_story(strategy)

    def compile_prompt(self, story):
        self.calls.append("compile_prompt")
        return self._d.compile_prompt(story)


class FailingProvider(RecordingProvider):
    """Raises inside generate_story to exercise engine-failure propagation."""

    def generate_story(self, strategy):
        raise RuntimeError("story engine boom")


def test_affiliate_url_accepted():
    result = HydraPipeline().run(AFFILIATE_URL)
    assert isinstance(result, RenderPrompt)


def test_direct_coupang_url_accepted():
    result = HydraPipeline().run(DIRECT_URL)
    assert isinstance(result, RenderPrompt)


def test_engines_run_in_correct_order_and_provider_called_correctly():
    provider = RecordingProvider()
    HydraPipeline(provider=provider).run(DIRECT_URL)
    assert provider.calls == [
        "analyze_product",
        "generate_creative_strategy",
        "generate_story",
        "compile_prompt",
    ]
    # Market Fit ran between analysis and strategy and fed the strategy call.
    _, market_fit_arg = provider.creative_args
    assert "market_fit_score" in market_fit_arg
    assert "decision" in market_fit_arg


def test_render_prompt_returned():
    result = HydraPipeline(provider=RecordingProvider()).run(DIRECT_URL)
    assert type(result) is RenderPrompt
    assert result.target_backend == "Higgsfield"


def test_invalid_url_rejected():
    pipeline = HydraPipeline()
    with pytest.raises(ValueError):
        pipeline.run("https://www.amazon.com/dp/B000000000")
    with pytest.raises(ValueError):
        pipeline.run("")


def test_engine_exception_propagates():
    provider = FailingProvider()
    with pytest.raises(RuntimeError, match="story engine boom"):
        HydraPipeline(provider=provider).run(DIRECT_URL)
    # Execution stopped at the story stage; the compiler never ran.
    assert "compile_prompt" not in provider.calls


def test_no_network(monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", _boom)
    result = HydraPipeline().run(AFFILIATE_URL)
    assert isinstance(result, RenderPrompt)
