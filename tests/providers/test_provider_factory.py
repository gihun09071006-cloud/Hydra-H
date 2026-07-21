"""Unit tests for the provider factory (mock/live mode selection)."""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from providers.base.provider import AIProvider  # noqa: E402
from providers.claude.claude_provider import ClaudeProvider  # noqa: E402
from providers.claude.mock_claude_provider import MockClaudeProvider  # noqa: E402
from providers.factory import ProviderFactory  # noqa: E402


def test_default_mode_returns_mock_claude(monkeypatch):
    monkeypatch.delenv("HYDRA_AI_MODE", raising=False)
    provider = ProviderFactory.create("claude")
    assert isinstance(provider, MockClaudeProvider)
    assert isinstance(provider, AIProvider)


def test_mock_mode_returns_mock_claude(monkeypatch):
    monkeypatch.setenv("HYDRA_AI_MODE", "mock")
    assert isinstance(ProviderFactory.create("claude"), MockClaudeProvider)


def test_live_mode_returns_real_claude(monkeypatch):
    monkeypatch.setenv("HYDRA_AI_MODE", "live")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-used")
    provider = ProviderFactory.create("claude")
    assert isinstance(provider, ClaudeProvider)


def test_live_mode_without_api_key_raises(monkeypatch):
    monkeypatch.setenv("HYDRA_AI_MODE", "live")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ValueError):
        ProviderFactory.create("claude")


def test_invalid_mode_does_not_fall_back(monkeypatch):
    monkeypatch.setenv("HYDRA_AI_MODE", "sandbox")
    with pytest.raises(ValueError):
        ProviderFactory.create("claude")


def test_case_insensitive(monkeypatch):
    monkeypatch.delenv("HYDRA_AI_MODE", raising=False)
    assert isinstance(ProviderFactory.create("Claude"), AIProvider)
    assert isinstance(ProviderFactory.create("CLAUDE"), AIProvider)


def test_unknown_provider_raises_value_error():
    with pytest.raises(ValueError):
        ProviderFactory.create("openai")
    with pytest.raises(ValueError):
        ProviderFactory.create("")
    with pytest.raises(ValueError):
        ProviderFactory.create(None)


def test_available_lists_claude():
    assert "claude" in ProviderFactory.available()


def test_register_extends_factory(monkeypatch):
    monkeypatch.delenv("HYDRA_AI_MODE", raising=False)

    class DummyProvider(MockClaudeProvider):
        name = "dummy"

    try:
        ProviderFactory.register("dummy", DummyProvider)
        assert isinstance(ProviderFactory.create("dummy"), DummyProvider)
    finally:
        ProviderFactory._providers.pop("dummy", None)


def test_register_rejects_non_provider():
    with pytest.raises(TypeError):
        ProviderFactory.register("bad", object)
