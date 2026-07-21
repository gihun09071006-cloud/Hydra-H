"""Unit tests for the Claude provider (placeholder).

Verifies interface implementation, deterministic outputs, contract shapes, and
that no external/network calls occur.
"""

import json
import socket
import sys
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from providers.base.provider import AIProvider  # noqa: E402
from providers.claude.claude_provider import ClaudeProvider  # noqa: E402

PI_SCHEMA_PATH = REPO_ROOT / "data" / "schemas" / "product_intelligence.schema.json"

INTERFACE_METHODS = (
    "analyze_product",
    "generate_creative_strategy",
    "generate_story",
    "compile_prompt",
)


@pytest.fixture
def provider():
    return ClaudeProvider()


def test_abstract_base_cannot_be_instantiated():
    with pytest.raises(TypeError):
        AIProvider()  # abstract


def test_base_methods_raise_not_implemented():
    class Stub(AIProvider):
        def analyze_product(self, product_facts):
            return super().analyze_product(product_facts)

        def generate_creative_strategy(self, product_intelligence):
            return super().generate_creative_strategy(product_intelligence)

        def generate_story(self, strategy):
            return super().generate_story(strategy)

        def compile_prompt(self, story):
            return super().compile_prompt(story)

    stub = Stub()
    with pytest.raises(NotImplementedError):
        stub.analyze_product({})
    with pytest.raises(NotImplementedError):
        stub.generate_creative_strategy({})
    with pytest.raises(NotImplementedError):
        stub.generate_story({})
    with pytest.raises(NotImplementedError):
        stub.compile_prompt({})


def test_claude_implements_all_interface_methods(provider):
    for method in INTERFACE_METHODS:
        assert callable(getattr(provider, method))


def test_analyze_product_matches_product_intelligence_schema(provider):
    schema = json.loads(PI_SCHEMA_PATH.read_text(encoding="utf-8"))
    result = provider.analyze_product({"product_name": "Test", "brand": "B", "features": ["x", "y"]})
    jsonschema.validate(instance=result, schema=schema)


def test_creative_strategy_contract(provider):
    result = provider.generate_creative_strategy({})
    assert set(result) == {
        "strategy", "reason", "confidence", "hook_type", "story_pattern", "cta_style",
    }
    assert 0 <= result["confidence"] <= 100


def test_story_contract(provider):
    result = provider.generate_story({"story_pattern": "Before → After"})
    assert result["story_pattern"] == "Before → After"
    assert result["duration"] == sum(s["duration"] for s in result["scenes"])
    goals = [s["goal"] for s in result["scenes"]]
    assert goals == ["Hook", "Problem", "Solution", "Proof", "CTA"]


def test_prompt_contract(provider):
    result = provider.compile_prompt({"duration": 20})
    assert result["target_backend"] == "Higgsfield"
    assert result["prompt"]
    assert set(result["metadata"]) == {"duration", "aspect_ratio", "language", "version"}


def test_outputs_are_deterministic(provider):
    facts = {"product_name": "Test", "features": ["a", "b", "c"]}
    assert provider.analyze_product(facts) == provider.analyze_product(facts)
    assert provider.generate_creative_strategy({}) == provider.generate_creative_strategy({})
    assert provider.generate_story({}) == provider.generate_story({})
    assert provider.compile_prompt({}) == provider.compile_prompt({})


def test_no_external_calls(provider, monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", _boom)
    # None of these may open a socket.
    pi = provider.analyze_product({"product_name": "X"})
    strategy = provider.generate_creative_strategy(pi)
    story = provider.generate_story(strategy)
    provider.compile_prompt(story)
