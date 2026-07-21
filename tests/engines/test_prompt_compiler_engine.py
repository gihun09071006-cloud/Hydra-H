"""Unit tests for the Prompt Compiler Engine (orchestration)."""

import socket
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from contracts.render_prompt import RenderPrompt  # noqa: E402
from contracts.storyboard import Scene, Storyboard  # noqa: E402
from engines.prompt_compiler_engine import PromptCompilerEngine  # noqa: E402
from providers.base.provider import AIProvider  # noqa: E402
from providers.claude.claude_provider import ClaudeProvider  # noqa: E402


class SpyProvider(AIProvider):
    """Counts compile_prompt calls; optionally returns/raises."""

    name = "spy"

    def __init__(self, result=None, raises: Exception | None = None):
        self.calls = 0
        self.last_arg = None
        self._result = result
        self._raises = raises
        self._delegate = ClaudeProvider()

    def analyze_product(self, product_facts):
        raise NotImplementedError

    def generate_creative_strategy(self, product_intelligence, market_fit_result=None):
        raise NotImplementedError

    def generate_story(self, strategy):
        raise NotImplementedError

    def compile_prompt(self, story):
        self.calls += 1
        self.last_arg = story
        if self._raises is not None:
            raise self._raises
        if self._result is not None:
            return self._result
        return self._delegate.compile_prompt(story)


VALID_STORYBOARD = Storyboard(
    story_pattern="Problem → Solution",
    duration=20,
    scenes=[
        Scene(scene=1, duration=3, goal="Hook", description="Open"),
        Scene(scene=2, duration=17, goal="CTA", description="Close"),
    ],
)


def test_engine_requires_a_provider():
    with pytest.raises(TypeError):
        PromptCompilerEngine(object())


def test_valid_storyboard_returns_render_prompt():
    engine = PromptCompilerEngine(SpyProvider())
    result = engine.compile(VALID_STORYBOARD)
    assert isinstance(result, RenderPrompt)
    assert result.target_backend
    assert result.metadata.duration == 20


def test_invalid_storyboard_rejected():
    engine = PromptCompilerEngine(SpyProvider())
    with pytest.raises(TypeError):
        engine.compile({"story_pattern": "X"})  # wrong type
    with pytest.raises(ValueError):
        engine.compile(Storyboard())  # no scenes


def test_provider_called_exactly_once():
    provider = SpyProvider()
    PromptCompilerEngine(provider).compile(VALID_STORYBOARD)
    assert provider.calls == 1
    assert isinstance(provider.last_arg, dict)  # provider receives a dict


def test_returned_object_is_render_prompt():
    result = PromptCompilerEngine(ClaudeProvider()).compile(VALID_STORYBOARD)
    assert type(result) is RenderPrompt


def test_invalid_provider_output_rejected():
    with pytest.raises(ValueError):
        PromptCompilerEngine(SpyProvider(result={"target_backend": "X"})).compile(VALID_STORYBOARD)
    with pytest.raises(TypeError):
        PromptCompilerEngine(SpyProvider(result="not a dict")).compile(VALID_STORYBOARD)
    with pytest.raises(ValueError):
        PromptCompilerEngine(SpyProvider(result={
            "target_backend": "Higgsfield", "prompt": "p",
            "negative_prompt": "n", "metadata": "nope",
        })).compile(VALID_STORYBOARD)


def test_provider_exceptions_propagate():
    provider = SpyProvider(raises=RuntimeError("provider boom"))
    with pytest.raises(RuntimeError, match="provider boom"):
        PromptCompilerEngine(provider).compile(VALID_STORYBOARD)


def test_engine_does_not_network(monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", _boom)
    result = PromptCompilerEngine(ClaudeProvider()).compile(VALID_STORYBOARD)
    assert isinstance(result, RenderPrompt)
