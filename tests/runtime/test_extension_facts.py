"""Tests for mapping browser-extension JSON into ProductFacts."""

import copy
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from contracts.product_facts import ProductFacts  # noqa: E402
from runtime.extension_facts import product_facts_from_extension  # noqa: E402

FIXTURE = REPO_ROOT / "tests" / "fixtures" / "coupang_extension_sample.json"


def _sample():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_valid_extension_json_maps_to_product_facts():
    facts = product_facts_from_extension(_sample())
    assert isinstance(facts, ProductFacts)  # existing contract reused
    assert facts.product_name == "Cordless Neck & Shoulder Massager"
    assert facts.price == 39900.0
    assert facts.currency == "KRW"
    assert facts.marketplace == "coupang"


def test_seller_maps_to_seller_name():
    facts = product_facts_from_extension(_sample())
    assert facts.seller_name == "RelaxPro Official Store"


def test_main_image_and_source_and_affiliate_mapping():
    facts = product_facts_from_extension(_sample())
    assert facts.main_image_url == "https://image.coupang.com/products/massager-main.jpg"
    assert facts.image_urls[1] == "https://image.coupang.com/products/massager-2.jpg"
    assert facts.source_url.startswith("https://www.coupang.com/vp/products/")
    assert facts.affiliate_url == "https://link.coupang.com/a/fyAfUSA2c8"


def test_missing_optional_fields_allowed():
    data = _sample()
    for optional in ("affiliate_url", "features", "rating", "review_count", "seller", "description"):
        data.pop(optional, None)
    facts = product_facts_from_extension(data)
    assert isinstance(facts, ProductFacts)
    assert facts.features == []
    assert facts.rating is None
    assert facts.seller_name is None


@pytest.mark.parametrize("missing", ["product_name", "product_url"])
def test_missing_required_fields_rejected(missing):
    data = _sample()
    data.pop(missing)
    with pytest.raises(ValueError):
        product_facts_from_extension(data)


def test_non_object_rejected():
    with pytest.raises(ValueError):
        product_facts_from_extension([1, 2, 3])


def test_invalid_price_type_rejected():
    data = _sample()
    data["price"] = "expensive"
    with pytest.raises(ValueError):
        product_facts_from_extension(data)


def test_invalid_image_urls_type_rejected():
    data = _sample()
    data["image_urls"] = "not-a-list"
    with pytest.raises(ValueError):
        product_facts_from_extension(data)


def test_unsupported_marketplace_rejected():
    data = _sample()
    data["marketplace"] = "amazon"
    with pytest.raises(ValueError):
        product_facts_from_extension(data)


def test_null_price_allowed():
    data = _sample()
    data["price"] = None
    facts = product_facts_from_extension(data)
    assert facts.price is None
