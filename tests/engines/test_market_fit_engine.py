"""Unit tests for the Market Fit Engine.

Verifies low / medium / high score products, the decision thresholds, and that
the output validates against the existing Market Fit schema.
"""

import json
import sys
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engines.market_fit_engine import MarketFitEngine, decide, evaluate  # noqa: E402

SCHEMA_PATH = REPO_ROOT / "data" / "schemas" / "market_fit.schema.json"
PI_SCHEMA_PATH = REPO_ROOT / "data" / "schemas" / "product_intelligence.schema.json"


def _product_intelligence(
    *,
    visual_proof,
    before_after,
    transformation,
    demonstrable,
    pain_severity,
    objection_probability,
    virality,
    alternatives,
    secondary_functions,
    offline="",
    diy="",
    why_buy="",
):
    """Build a Product Intelligence object with tunable strength signals."""
    return {
        "product_identity": {
            "product_name": "Test Product",
            "brand": "TestBrand",
            "category": "Test",
            "price": {"amount": 29.99, "currency": "USD"},
            "country": "United States",
            "marketplace": "Coupang",
        },
        "functional_analysis": {
            "primary_function": "Do the thing",
            "secondary_functions": secondary_functions,
            "top_features": ["A", "B", "C"],
            "usp": "The only one that does the thing",
        },
        "visual_analysis": {
            "benefit_visually_demonstrable": demonstrable,
            "visual_proof_strength": visual_proof,
            "before_after_possible": before_after,
            "transformation_possible": transformation,
        },
        "customer_analysis": {
            "primary_target": "People",
            "secondary_target": "Other people",
            "buying_situation": "When needed",
            "daily_usage": "Daily",
            "emotional_motivation": "Feel good",
            "functional_motivation": "Get results",
        },
        "pain_analysis": [
            {"problem": "The main problem", "severity": pain_severity, "rank": 1},
        ],
        "objection_analysis": [
            {"objection": "Not sure it works", "probability": objection_probability, "rank": 1},
        ],
        "competitive_analysis": {
            "existing_alternatives": alternatives,
            "offline_alternative": offline,
            "diy_alternative": diy,
            "why_buy_this_instead": why_buy,
        },
        "virality_analysis": {
            "scroll_stop_potential": virality,
            "surprise_potential": virality,
            "satisfaction_potential": virality,
            "shareability": virality,
            "comment_potential": virality,
        },
        "platform_recommendation": {
            "primary_platform": "Instagram Reels",
            "reason": "Fits short vertical video",
        },
    }


HIGH = _product_intelligence(
    visual_proof=95, before_after=True, transformation=True, demonstrable=True,
    pain_severity=90, objection_probability=20, virality=90, alternatives=[],
    secondary_functions=["s1", "s2"], offline="Therapy", diy="DIY", why_buy="It is better",
)
MEDIUM = _product_intelligence(
    visual_proof=65, before_after=True, transformation=False, demonstrable=True,
    pain_severity=60, objection_probability=50, virality=57,
    alternatives=["Alt1", "Alt2"], secondary_functions=["s1"],
    offline="Therapy", diy="", why_buy="It is better",
)
LOW = _product_intelligence(
    visual_proof=10, before_after=False, transformation=False, demonstrable=False,
    pain_severity=20, objection_probability=90, virality=15,
    alternatives=["Alt1", "Alt2", "Alt3", "Alt4", "Alt5"], secondary_functions=[],
    offline="", diy="", why_buy="",
)


@pytest.fixture
def schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def engine():
    return MarketFitEngine()


def test_inputs_are_valid_product_intelligence():
    pi_schema = json.loads(PI_SCHEMA_PATH.read_text(encoding="utf-8"))
    for pi in (LOW, MEDIUM, HIGH):
        jsonschema.validate(instance=pi, schema=pi_schema)


def test_high_score_product(engine, schema):
    result = engine.evaluate(HIGH)
    jsonschema.validate(instance=result, schema=schema)
    assert result["market_fit_score"] >= 80
    assert result["decision"] in ("Create Immediately", "Priority A")


def test_medium_score_product(engine, schema):
    result = engine.evaluate(MEDIUM)
    jsonschema.validate(instance=result, schema=schema)
    assert 60 <= result["market_fit_score"] < 80
    assert result["decision"] in ("Priority B", "Optional")


def test_low_score_product(engine, schema):
    result = engine.evaluate(LOW)
    jsonschema.validate(instance=result, schema=schema)
    assert result["market_fit_score"] < 60
    assert result["decision"] == "Reject"


def test_scores_are_ordered():
    low = evaluate(LOW)["market_fit_score"]
    medium = evaluate(MEDIUM)["market_fit_score"]
    high = evaluate(HIGH)["market_fit_score"]
    assert low < medium < high


def test_decision_thresholds():
    assert decide(100) == "Create Immediately"
    assert decide(90) == "Create Immediately"
    assert decide(89) == "Priority A"
    assert decide(80) == "Priority A"
    assert decide(79) == "Priority B"
    assert decide(70) == "Priority B"
    assert decide(69) == "Optional"
    assert decide(60) == "Optional"
    assert decide(59) == "Reject"
    assert decide(0) == "Reject"


def test_strengths_and_weaknesses_shape(engine):
    result = engine.evaluate(HIGH)
    assert len(result["strengths"]) == 3
    assert len(result["weaknesses"]) == 3
    for item in result["strengths"] + result["weaknesses"]:
        assert item["reason"]  # every score carries a written reason
        assert 0 <= item["score"] <= 20


def test_recommendations_present(engine):
    result = engine.evaluate(HIGH)
    assert result["recommended_strategy"]
    assert result["recommended_hook_type"]
    assert 0 <= result["confidence"] <= 100
