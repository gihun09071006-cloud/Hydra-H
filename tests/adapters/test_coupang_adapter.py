"""Acceptance test for the Coupang Product Adapter.

Given a Coupang product URL, when the adapter is executed, then a valid Product
Intelligence object is returned that validates against the existing Product
Intelligence schema.
"""

import json
import sys
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from adapters.coupang.coupang_adapter import CoupangAdapter  # noqa: E402

SCHEMA_PATH = REPO_ROOT / "data" / "schemas" / "product_intelligence.schema.json"

VALID_URL = "https://www.coupang.com/vp/products/1234567890"


@pytest.fixture
def schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def adapter():
    return CoupangAdapter()


def test_validate_accepts_coupang_url(adapter):
    assert adapter.validate(VALID_URL) is True
    assert adapter.validate("https://m.coupang.com/vm/products/987654321") is True


def test_validate_rejects_non_coupang_url(adapter):
    assert adapter.validate("https://www.amazon.com/dp/B000000000") is False
    assert adapter.validate("https://www.coupang.com/np/categories/1") is False
    assert adapter.validate("not-a-url") is False
    assert adapter.validate("") is False


def test_analyze_returns_schema_valid_product_intelligence(adapter, schema):
    """Acceptance: the returned object validates against the schema."""
    result = adapter.analyze(VALID_URL)

    # Validates against the existing Product Intelligence schema.
    jsonschema.validate(instance=result, schema=schema)

    # Sanity: the record is attributed to Coupang.
    assert result["product_identity"]["marketplace"] == "Coupang"
    assert len(result["functional_analysis"]["top_features"]) == 3


def test_analyze_rejects_invalid_url(adapter):
    with pytest.raises(ValueError):
        adapter.analyze("https://www.amazon.com/dp/B000000000")


def test_schema_itself_is_valid(schema):
    """The schema must be a valid JSON Schema document."""
    jsonschema.Draft202012Validator.check_schema(schema)
