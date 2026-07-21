"""Unit tests for the Story Engine (orchestration)."""

import socket
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from contracts.creative_strategy import CreativeStrategy  # noqa: E402
from contracts.storyboard import Storyboard  # noqa: E402
from engines.story_engine import StoryEngine  # noqa: E402
from providers.base.provider import AIProvider  # noqa: E402
from providers.claude.mock_claude_provider import MockClaudeProvider  # noqa: E402


class SpyProvider(AIProvider):
    """Counts generate_story calls; optionally returns/raises."""

    name = "spy"

    def __init__(self, result=None, raises: Exception | None = None):
        self.calls = 0
        self.last_arg = None
        self._result = result
        self._raises = raises
        self._delegate = MockClaudeProvider()

    def analyze_product(self, product_facts):
        raise NotImplementedError

    def generate_creative_strategy(self, product_intelligence, market_fit_result=None):
        raise NotImplementedError

    def generate_story(self, strategy):
        self.calls += 1
        self.last_arg = strategy
        if self._raises is not None:
            raise self._raises
        if self._result is not None:
            return self._result
        return self._delegate.generate_story(strategy)

    def compile_prompt(self, story):
        raise NotImplementedError


VALID_STRATEGY = CreativeStrategy(
    strategy="Visual Demonstration", reason="fits", confidence=80,
    hook_type="Demonstration", story_pattern="Problem → Solution", cta_style="Direct",
)


def test_engine_requires_a_provider():
    with pytest.raises(TypeError):
        StoryEngine(object())


def test_valid_strategy_returns_storyboard():
    engine = StoryEngine(SpyProvider())
    result = engine.generate(VALID_STRATEGY)
    assert isinstance(result, Storyboard)
    assert result.scenes


def test_missing_optional_fields_still_generates():
    engine = StoryEngine(SpyProvider())
    result = engine.generate(CreativeStrategy(strategy="POV"))  # only the required field
    assert isinstance(result, Storyboard)


def test_invalid_strategy_rejected():
    engine = StoryEngine(SpyProvider())
    with pytest.raises(TypeError):
        engine.generate({"strategy": "X"})  # wrong type
    with pytest.raises(ValueError):
        engine.generate(CreativeStrategy())  # empty strategy


def test_provider_called_exactly_once():
    provider = SpyProvider()
    StoryEngine(provider).generate(VALID_STRATEGY)
    assert provider.calls == 1
    assert isinstance(provider.last_arg, dict)  # provider receives a dict


def test_returned_object_is_storyboard():
    result = StoryEngine(MockClaudeProvider()).generate(VALID_STRATEGY)
    assert type(result) is Storyboard


def test_invalid_provider_output_rejected():
    with pytest.raises(ValueError):
        StoryEngine(SpyProvider(result={"story_pattern": "X"})).generate(VALID_STRATEGY)
    with pytest.raises(TypeError):
        StoryEngine(SpyProvider(result="not a dict")).generate(VALID_STRATEGY)
    with pytest.raises(ValueError):
        StoryEngine(
            SpyProvider(result={"story_pattern": "X", "duration": 20, "scenes": "nope"})
        ).generate(VALID_STRATEGY)


def test_provider_exceptions_propagate():
    provider = SpyProvider(raises=RuntimeError("provider boom"))
    with pytest.raises(RuntimeError, match="provider boom"):
        StoryEngine(provider).generate(VALID_STRATEGY)


def test_engine_does_not_network(monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", _boom)
    result = StoryEngine(MockClaudeProvider()).generate(VALID_STRATEGY)
    assert isinstance(result, Storyboard)
