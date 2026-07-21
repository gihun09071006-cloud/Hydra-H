"""Unit tests for the provider factory."""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from providers.base.provider import AIProvider  # noqa: E402
from providers.claude.claude_provider import ClaudeProvider  # noqa: E402
from providers.factory import ProviderFactory  # noqa: E402


def test_factory_returns_claude_provider():
    provider = ProviderFactory.create("claude")
    assert isinstance(provider, ClaudeProvider)
    assert isinstance(provider, AIProvider)


def test_factory_is_case_insensitive():
    assert isinstance(ProviderFactory.create("Claude"), ClaudeProvider)
    assert isinstance(ProviderFactory.create("CLAUDE"), ClaudeProvider)


def test_unknown_provider_raises_value_error():
    with pytest.raises(ValueError):
        ProviderFactory.create("openai")
    with pytest.raises(ValueError):
        ProviderFactory.create("")
    with pytest.raises(ValueError):
        ProviderFactory.create(None)


def test_available_lists_claude():
    assert "claude" in ProviderFactory.available()


def test_register_extends_factory():
    class DummyProvider(ClaudeProvider):
        name = "dummy"

    try:
        ProviderFactory.register("dummy", DummyProvider)
        assert isinstance(ProviderFactory.create("dummy"), DummyProvider)
    finally:
        ProviderFactory._providers.pop("dummy", None)


def test_register_rejects_non_provider():
    with pytest.raises(TypeError):
        ProviderFactory.register("bad", object)
