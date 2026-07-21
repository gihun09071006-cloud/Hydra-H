"""Unit tests for the real Anthropic-backed ClaudeProvider.

Uses an injectable fake Anthropic client — no real network, no API key.
"""

import json
import socket
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from contracts.creative_strategy import CreativeStrategy  # noqa: E402
from contracts.product_intelligence import ProductIntelligence  # noqa: E402
from contracts.render_prompt import RenderPrompt  # noqa: E402
from contracts.storyboard import Storyboard  # noqa: E402
from providers.base.provider import AIProvider  # noqa: E402
from providers.claude.claude_provider import ClaudeProvider, ProviderConfigError  # noqa: E402
from providers.claude.mock_claude_provider import MockClaudeProvider  # noqa: E402
from providers.json_response_parser import ProviderResponseError  # noqa: E402

MOCK = MockClaudeProvider()


class FakeBlock:
    type = "text"

    def __init__(self, text):
        self.text = text


class FakeResponse:
    def __init__(self, text):
        self.content = [FakeBlock(text)]


class FakeMessages:
    def __init__(self, payload):
        self._payload = payload
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        text = self._payload if isinstance(self._payload, str) else json.dumps(self._payload)
        return FakeResponse(text)


class FakeClient:
    def __init__(self, payload):
        self.messages = FakeMessages(payload)


def _provider(payload):
    client = FakeClient(payload)
    return ClaudeProvider(client=client), client


def test_implements_all_interface_methods():
    provider = ClaudeProvider(client=FakeClient({}))
    assert isinstance(provider, AIProvider)
    for method in ("analyze_product", "generate_creative_strategy", "generate_story", "compile_prompt"):
        assert callable(getattr(provider, method))


def test_analyze_product_returns_contract_with_one_call():
    payload = MOCK.analyze_product({"product_name": "X", "features": ["a", "b"]})
    provider, client = _provider(payload)
    result = provider.analyze_product({"product_name": "X"})
    assert isinstance(result, ProductIntelligence)
    assert len(client.messages.calls) == 1
    call = client.messages.calls[0]
    assert call["model"]
    assert call["system"]
    assert call["messages"][0]["role"] == "user"


def test_generate_creative_strategy_returns_contract():
    payload = MOCK.generate_creative_strategy({})
    provider, client = _provider(payload)
    result = provider.generate_creative_strategy(
        ProductIntelligence().to_dict(), {"market_fit_score": 80, "decision": "Priority A"}
    )
    assert isinstance(result, CreativeStrategy)
    assert len(client.messages.calls) == 1


def test_generate_story_returns_contract():
    payload = MOCK.generate_story({})
    provider, client = _provider(payload)
    result = provider.generate_story(CreativeStrategy(strategy="X").to_dict())
    assert isinstance(result, Storyboard)
    assert len(client.messages.calls) == 1


def test_compile_prompt_returns_contract():
    payload = MOCK.compile_prompt({})
    provider, client = _provider(payload)
    result = provider.compile_prompt(Storyboard().to_dict())
    assert isinstance(result, RenderPrompt)
    assert len(client.messages.calls) == 1


def test_missing_required_keys_rejected():
    provider, _ = _provider({"unexpected": 1})
    with pytest.raises(ProviderResponseError):
        provider.analyze_product({"product_name": "X"})


def test_markdown_fence_response_rejected():
    provider, _ = _provider('```json\n{"a": 1}\n```')
    with pytest.raises(ProviderResponseError):
        provider.analyze_product({"product_name": "X"})


def test_injected_client_prevents_default_build():
    # No ANTHROPIC_API_KEY and no anthropic import are needed when a client is injected.
    payload = MOCK.compile_prompt({})
    provider, _ = _provider(payload)
    assert isinstance(provider.compile_prompt(Storyboard().to_dict()), RenderPrompt)


def test_default_client_requires_configuration(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    provider = ClaudeProvider()  # no injected client
    with pytest.raises(ProviderConfigError):
        provider.analyze_product({"product_name": "X"})


def test_no_network_with_injected_client(monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", _boom)
    payload = MOCK.analyze_product({"product_name": "X"})
    provider, _ = _provider(payload)
    assert isinstance(provider.analyze_product({"product_name": "X"}), ProductIntelligence)
