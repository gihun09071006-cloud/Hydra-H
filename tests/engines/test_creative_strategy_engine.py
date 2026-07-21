"""Unit tests for the Creative Strategy Engine (orchestration)."""

import socket
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from contracts.creative_strategy import CreativeStrategy  # noqa: E402
from contracts.product_intelligence import ProductIntelligence  # noqa: E402
from engines.creative_strategy_engine import CreativeStrategyEngine  # noqa: E402
from providers.base.provider import AIProvider  # noqa: E402
from providers.claude.mock_claude_provider import MockClaudeProvider  # noqa: E402


class SpyProvider(AIProvider):
    """Counts generate_creative_strategy calls; optionally returns/raises."""

    name = "spy"

    def __init__(self, result=None, raises: Exception | None = None):
        self.calls = 0
        self.last_args = None
        self._result = result
        self._raises = raises
        self._delegate = MockClaudeProvider()

    def analyze_product(self, product_facts):
        raise NotImplementedError

    def generate_creative_strategy(self, product_intelligence, market_fit_result=None):
        self.calls += 1
        self.last_args = (product_intelligence, market_fit_result)
        if self._raises is not None:
            raise self._raises
        if self._result is not None:
            return self._result
        return self._delegate.generate_creative_strategy(product_intelligence, market_fit_result)

    def generate_story(self, strategy):
        raise NotImplementedError

    def compile_prompt(self, story):
        raise NotImplementedError


def _product_intelligence(name="Cordless Massager"):
    pi = ProductIntelligence()
    pi.product_identity.product_name = name
    return pi


VALID_MARKET_FIT = {
    "market_fit_score": 85,
    "decision": "Priority A",
    "strengths": [],
    "weaknesses": [],
    "recommended_strategy": "Visual Demonstration",
    "recommended_hook_type": "Demonstration",
    "confidence": 80,
}


def test_engine_requires_a_provider():
    with pytest.raises(TypeError):
        CreativeStrategyEngine(object())


def test_valid_inputs_return_creative_strategy():
    engine = CreativeStrategyEngine(SpyProvider())
    result = engine.decide(_product_intelligence(), VALID_MARKET_FIT)
    assert isinstance(result, CreativeStrategy)
    assert result.strategy


def test_missing_optional_fields_still_decides():
    # A minimal Market Fit result carrying only the required keys.
    engine = CreativeStrategyEngine(SpyProvider())
    minimal_mf = {"market_fit_score": 60, "decision": "Optional"}
    result = engine.decide(_product_intelligence("Only a name"), minimal_mf)
    assert isinstance(result, CreativeStrategy)


def test_invalid_product_intelligence_rejected():
    engine = CreativeStrategyEngine(SpyProvider())
    with pytest.raises(TypeError):
        engine.decide({"product_identity": {}}, VALID_MARKET_FIT)  # wrong type
    with pytest.raises(ValueError):
        engine.decide(ProductIntelligence(), VALID_MARKET_FIT)  # empty product_name


def test_invalid_market_fit_rejected():
    engine = CreativeStrategyEngine(SpyProvider())
    with pytest.raises(TypeError):
        engine.decide(_product_intelligence(), "not a dict")
    with pytest.raises(ValueError):
        engine.decide(_product_intelligence(), {"decision": "Priority A"})  # no score


def test_provider_called_exactly_once_with_both_inputs():
    provider = SpyProvider()
    engine = CreativeStrategyEngine(provider)
    engine.decide(_product_intelligence(), VALID_MARKET_FIT)
    assert provider.calls == 1
    pi_arg, mf_arg = provider.last_args
    assert isinstance(pi_arg, dict)  # provider receives the PI as a dict
    assert mf_arg == VALID_MARKET_FIT


def test_returned_object_is_creative_strategy():
    result = CreativeStrategyEngine(MockClaudeProvider()).decide(
        _product_intelligence(), VALID_MARKET_FIT
    )
    assert type(result) is CreativeStrategy


def test_invalid_provider_output_rejected():
    with pytest.raises(ValueError):
        CreativeStrategyEngine(SpyProvider(result={"strategy": "X"})).decide(
            _product_intelligence(), VALID_MARKET_FIT
        )
    with pytest.raises(TypeError):
        CreativeStrategyEngine(SpyProvider(result="not a dict")).decide(
            _product_intelligence(), VALID_MARKET_FIT
        )


def test_provider_exceptions_propagate():
    provider = SpyProvider(raises=RuntimeError("provider boom"))
    engine = CreativeStrategyEngine(provider)
    with pytest.raises(RuntimeError, match="provider boom"):
        engine.decide(_product_intelligence(), VALID_MARKET_FIT)


def test_engine_does_not_network(monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", _boom)
    result = CreativeStrategyEngine(MockClaudeProvider()).decide(
        _product_intelligence(), VALID_MARKET_FIT
    )
    assert isinstance(result, CreativeStrategy)
