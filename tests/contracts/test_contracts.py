"""Unit tests for the internal AI contracts.

Verifies serialization, deserialization (round-trip), equality, and default
values for every contract.
"""

import json
import sys
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from contracts import (  # noqa: E402
    CreativeStrategy,
    Price,
    ProductFacts,
    ProductIntelligence,
    RenderPrompt,
    Scene,
    Storyboard,
)

PI_SCHEMA_PATH = REPO_ROOT / "data" / "schemas" / "product_intelligence.schema.json"


def _full_product_intelligence():
    return ProductIntelligence.from_dict({
        "product_identity": {
            "product_name": "Cordless Massager",
            "brand": "RelaxPro",
            "category": "Health",
            "price": {"amount": 39900, "currency": "KRW"},
            "country": "South Korea",
            "marketplace": "Coupang",
        },
        "functional_analysis": {
            "primary_function": "Relieve tension",
            "secondary_functions": ["Improve circulation"],
            "top_features": ["Cordless", "Heat", "Adjustable"],
            "usp": "Cordless deep-kneading with heat",
        },
        "visual_analysis": {
            "benefit_visually_demonstrable": True,
            "visual_proof_strength": 82,
            "before_after_possible": True,
            "transformation_possible": False,
        },
        "customer_analysis": {
            "primary_target": "Office workers",
            "secondary_target": "Older adults",
            "buying_situation": "After desk work",
            "daily_usage": "Evenings",
            "emotional_motivation": "Relief",
            "functional_motivation": "Reduce pain",
        },
        "pain_analysis": [{"problem": "Neck tension", "severity": 80, "rank": 1}],
        "objection_analysis": [{"objection": "Strong enough?", "probability": 60, "rank": 1}],
        "competitive_analysis": {
            "existing_alternatives": ["Manual tools"],
            "offline_alternative": "Massage therapy",
            "diy_alternative": "Stretching",
            "why_buy_this_instead": "On-demand deep kneading",
        },
        "virality_analysis": {
            "scroll_stop_potential": 72,
            "surprise_potential": 58,
            "satisfaction_potential": 85,
            "shareability": 60,
            "comment_potential": 55,
        },
        "platform_recommendation": {
            "primary_platform": "Instagram Reels",
            "reason": "Fits vertical relief content",
        },
    })


# -- default values ---------------------------------------------------------

def test_default_values():
    assert ProductFacts() == ProductFacts(
        product_name=None, brand=None, price=None, currency=None, category=None,
        main_image_url=None, description=None, features=[], seller_name=None,
        marketplace=None, country=None,
    )
    assert ProductFacts().features == []
    assert CreativeStrategy().confidence == 0
    assert Storyboard().duration == 20
    assert Storyboard().scenes == []
    assert RenderPrompt().metadata.version == ""
    assert ProductIntelligence().product_identity.price == Price(amount=0, currency="")


# -- serialization / deserialization round-trips ----------------------------

@pytest.mark.parametrize("obj", [
    ProductFacts(product_name="X", price=9.99, features=["a", "b"]),
    CreativeStrategy(strategy="Visual Demonstration", confidence=80, cta_style="Direct"),
    Storyboard(story_pattern="Before → After", duration=20, scenes=[
        Scene(scene=1, duration=3, goal="Hook", description="Open"),
        Scene(scene=2, duration=17, goal="CTA", description="Close"),
    ]),
    RenderPrompt(target_backend="Higgsfield", prompt="p", negative_prompt="n"),
])
def test_round_trip(obj):
    restored = type(obj).from_dict(obj.to_dict())
    assert restored == obj


def test_product_intelligence_round_trip():
    pi = _full_product_intelligence()
    assert ProductIntelligence.from_dict(pi.to_dict()) == pi


def test_to_dict_is_plain_data():
    d = CreativeStrategy(strategy="POV").to_dict()
    assert isinstance(d, dict)
    assert d["strategy"] == "POV"
    assert json.dumps(d)  # serializable to JSON


# -- equality ---------------------------------------------------------------

def test_equality():
    assert CreativeStrategy(strategy="POV") == CreativeStrategy(strategy="POV")
    assert CreativeStrategy(strategy="POV") != CreativeStrategy(strategy="UGC Review")
    assert _full_product_intelligence() == _full_product_intelligence()


# -- cross-check the dataclass mirrors the schema ---------------------------

def test_product_intelligence_matches_schema():
    schema = json.loads(PI_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=_full_product_intelligence().to_dict(), schema=schema)
