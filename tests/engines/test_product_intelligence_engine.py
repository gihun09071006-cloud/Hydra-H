"""Unit tests for the Product Intelligence Engine (orchestration)."""

import socket
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from contracts.product_facts import ProductFacts  # noqa: E402
from contracts.product_intelligence import ProductIntelligence  # noqa: E402
from engines.product_intelligence_engine import ProductIntelligenceEngine  # noqa: E402
from providers.base.provider import AIProvider  # noqa: E402
from providers.claude.mock_claude_provider import MockClaudeProvider  # noqa: E402


class SpyProvider(AIProvider):
    """Counts analyze_product calls; optionally returns/raises a fixed result."""

    name = "spy"

    def __init__(self, result=None, raises: Exception | None = None):
        self.calls = 0
        self._result = result
        self._raises = raises
        self._delegate = MockClaudeProvider()

    def analyze_product(self, product_facts):
        self.calls += 1
        if self._raises is not None:
            raise self._raises
        if self._result is not None:
            return self._result
        return self._delegate.analyze_product(product_facts)

    def generate_creative_strategy(self, product_intelligence):
        raise NotImplementedError

    def generate_story(self, strategy):
        raise NotImplementedError

    def compile_prompt(self, story):
        raise NotImplementedError


VALID_FACTS = ProductFacts(
    product_name="Cordless Massager", brand="RelaxPro", price=39900,
    currency="KRW", category="Health", features=["Cordless", "Heat"],
)


def test_engine_requires_a_provider():
    with pytest.raises(TypeError):
        ProductIntelligenceEngine(object())


def test_valid_product_facts_returns_product_intelligence():
    provider = SpyProvider()
    engine = ProductIntelligenceEngine(provider)
    result = engine.analyze(VALID_FACTS)
    assert isinstance(result, ProductIntelligence)
    assert result.product_identity.product_name


def test_missing_optional_fields_still_analyzes():
    provider = SpyProvider()
    engine = ProductIntelligenceEngine(provider)
    result = engine.analyze(ProductFacts(product_name="Only a name"))
    assert isinstance(result, ProductIntelligence)


def test_invalid_product_facts_raise():
    engine = ProductIntelligenceEngine(SpyProvider())
    # Wrong type.
    with pytest.raises(TypeError):
        engine.analyze({"product_name": "X"})
    # Missing required product_name.
    with pytest.raises(ValueError):
        engine.analyze(ProductFacts())


def test_provider_called_exactly_once():
    provider = SpyProvider()
    ProductIntelligenceEngine(provider).analyze(VALID_FACTS)
    assert provider.calls == 1


def test_returned_object_is_product_intelligence():
    result = ProductIntelligenceEngine(MockClaudeProvider()).analyze(VALID_FACTS)
    assert type(result) is ProductIntelligence


def test_provider_exceptions_propagate():
    provider = SpyProvider(raises=RuntimeError("provider boom"))
    engine = ProductIntelligenceEngine(provider)
    with pytest.raises(RuntimeError, match="provider boom"):
        engine.analyze(VALID_FACTS)


def test_incomplete_provider_result_raises():
    provider = SpyProvider(result={"product_identity": {}})
    engine = ProductIntelligenceEngine(provider)
    with pytest.raises(ValueError):
        engine.analyze(VALID_FACTS)


def test_non_dict_provider_result_raises():
    provider = SpyProvider(result="not a dict")
    engine = ProductIntelligenceEngine(provider)
    with pytest.raises(TypeError):
        engine.analyze(VALID_FACTS)


def test_engine_does_not_network(monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", _boom)
    result = ProductIntelligenceEngine(MockClaudeProvider()).analyze(VALID_FACTS)
    assert isinstance(result, ProductIntelligence)
