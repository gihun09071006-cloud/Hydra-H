"""Acceptance tests for the Product Intelligence Parser.

Covers valid sample HTML, missing optional fields, invalid HTML, and validation
of the output against the existing Product Intelligence schema.
"""

import json
import sys
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from parsers.product_parser import ProductParser  # noqa: E402

SCHEMA_PATH = REPO_ROOT / "data" / "schemas" / "product_intelligence.schema.json"
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "coupang_product_sample.html"


@pytest.fixture
def schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def parser():
    return ProductParser()


@pytest.fixture
def sample_html():
    return FIXTURE_PATH.read_text(encoding="utf-8")


def test_valid_sample_html(parser, sample_html, schema):
    extracted = parser.extract(sample_html)
    assert extracted["product_name"] == "Cordless Neck & Shoulder Massager"
    assert extracted["brand"] == "RelaxPro"
    assert extracted["price"] == 39900.0
    assert extracted["currency"] == "KRW"
    assert extracted["category"] == "Health & Wellness"
    assert extracted["main_image_url"].endswith("massager-main.jpg")
    assert "heat therapy" in extracted["description"].lower()
    assert extracted["features"][:3] == [
        "Cordless wearable design",
        "Heat therapy",
        "Adjustable intensity",
    ]
    assert extracted["seller_name"] == "RelaxPro Official Store"

    pi = parser.to_product_intelligence(extracted, marketplace="Coupang", country="South Korea")
    jsonschema.validate(instance=pi, schema=schema)
    assert pi["product_identity"]["product_name"] == "Cordless Neck & Shoulder Massager"
    assert pi["product_identity"]["price"] == {"amount": 39900.0, "currency": "KRW"}
    assert pi["product_identity"]["marketplace"] == "Coupang"
    assert len(pi["functional_analysis"]["top_features"]) == 3


def test_missing_optional_fields(parser, schema):
    html = '<html><head><meta property="og:title" content="Basic Product"></head><body></body></html>'
    extracted = parser.extract(html)

    # Present value is extracted...
    assert extracted["product_name"] == "Basic Product"
    # ...and missing values are null / empty, never fabricated.
    assert extracted["brand"] is None
    assert extracted["price"] is None
    assert extracted["currency"] is None
    assert extracted["category"] is None
    assert extracted["features"] == []
    assert extracted["seller_name"] is None

    pi = parser.parse(html)
    jsonschema.validate(instance=pi, schema=schema)
    assert pi["product_identity"]["product_name"] == "Basic Product"
    assert pi["product_identity"]["brand"] == ""
    assert pi["product_identity"]["price"] == {"amount": 0, "currency": ""}
    assert pi["functional_analysis"]["top_features"] == ["", "", ""]


@pytest.mark.parametrize("html", ["", "<<< not really html >>>", "\x00\x01 garbage"])
def test_invalid_html_does_not_crash_and_validates(parser, schema, html):
    extracted = parser.extract(html)
    assert extracted["product_name"] is None
    assert extracted["features"] == []

    pi = parser.parse(html)
    jsonschema.validate(instance=pi, schema=schema)


def test_schema_validation(parser, sample_html, schema):
    """The schema is a valid document and the parser output conforms to it."""
    jsonschema.Draft202012Validator.check_schema(schema)
    pi = parser.parse(sample_html, marketplace="Coupang")
    jsonschema.validate(instance=pi, schema=schema)
