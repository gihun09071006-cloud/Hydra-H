"""Extraction-contract tests for the browser extension.

The extraction runs as JavaScript in Chrome, so these tests verify the
normalized output contract statically: every required field is built by
content.js, the fixed defaults are present, and only product pages are accepted.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXT = REPO_ROOT / "browser_extension"

# The normalized extraction shape (matches the task's output contract).
REQUIRED_FIELDS = [
    "marketplace",
    "affiliate_url",
    "product_url",
    "product_id",
    "item_id",
    "product_name",
    "price",
    "currency",
    "image_urls",
    "description",
    "features",
    "rating",
    "review_count",
    "seller",
    "captured_at",
]


def _content():
    return (EXT / "content.js").read_text(encoding="utf-8")


def test_content_builds_every_normalized_field():
    src = _content()
    for field in REQUIRED_FIELDS:
        assert f"{field}:" in src, f"missing field in content.js: {field}"


def test_fixed_defaults_present():
    src = _content()
    assert '"coupang"' in src  # marketplace default
    assert '"KRW"' in src  # currency default


def test_only_product_pages_supported():
    popup = (EXT / "popup.js").read_text(encoding="utf-8")
    # The popup gates extraction to rendered Coupang product pages.
    assert "/vp/products/" in popup


def test_shared_pipeline_field_names_reused():
    # Field names shared with the ProductFacts pipeline are reused verbatim.
    src = _content()
    for shared in ["product_name", "price", "currency", "description", "features", "marketplace"]:
        assert f"{shared}:" in src, shared
