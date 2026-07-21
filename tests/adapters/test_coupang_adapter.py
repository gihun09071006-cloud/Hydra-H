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

from adapters.coupang.coupang_adapter import (  # noqa: E402
    CoupangAdapter,
    CoupangConnectionError,
    CoupangHTTPError,
    CoupangTimeoutError,
    EmptyResponseError,
    InvalidCoupangURLError,
    InvalidRedirectError,
    NonHtmlResponseError,
)

SCHEMA_PATH = REPO_ROOT / "data" / "schemas" / "product_intelligence.schema.json"
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "coupang_product_sample.html"

VALID_URL = "https://www.coupang.com/vp/products/1234567890"
DIRECT_URL = "https://www.coupang.com/vp/products/1234567890"
AFFILIATE_URL = "https://link.coupang.com/a/example"
PRODUCT_HTML = FIXTURE_PATH.read_text(encoding="utf-8")


class FakeResponse:
    def __init__(self, *, status_code=200, url=DIRECT_URL, text=PRODUCT_HTML,
                 content_type="text/html; charset=utf-8"):
        self.status_code = status_code
        self.url = url
        self.text = text
        self.headers = {"Content-Type": content_type}


class FakeSession:
    def __init__(self, response=None, exc=None):
        self.response = response
        self.exc = exc
        self.calls = []

    def get(self, url, headers=None, timeout=None, allow_redirects=None):
        self.calls.append(
            {"url": url, "headers": headers, "timeout": timeout, "allow_redirects": allow_redirects}
        )
        if self.exc is not None:
            raise self.exc
        return self.response


def _adapter_with(response=None, exc=None):
    session = FakeSession(response=response, exc=exc)
    return CoupangAdapter(http_client=session), session


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


# -- fetch() over HTTP (mocked session) ------------------------------------

def test_fetch_direct_product_url_returns_html():
    adapter, session = _adapter_with(FakeResponse(url=DIRECT_URL))
    assert adapter.fetch(DIRECT_URL) == PRODUCT_HTML
    assert session.calls[0]["url"] == DIRECT_URL


def test_fetch_affiliate_follows_redirect():
    # The final URL differs from the affiliate URL (redirect followed by client).
    adapter, session = _adapter_with(FakeResponse(url=DIRECT_URL))
    assert adapter.fetch(AFFILIATE_URL) == PRODUCT_HTML
    # The adapter passes the ORIGINAL affiliate URL to the client (no manual parsing).
    assert session.calls[0]["url"] == AFFILIATE_URL


def test_fetch_sends_browser_headers_and_timeout():
    adapter, session = _adapter_with(FakeResponse(url=DIRECT_URL))
    adapter.fetch(DIRECT_URL)
    call = session.calls[0]
    assert "Mozilla" in call["headers"]["User-Agent"]
    assert "Accept" in call["headers"]
    assert "Accept-Language" in call["headers"]
    assert isinstance(call["timeout"], (int, float)) and call["timeout"] > 0
    assert call["allow_redirects"] is True


def test_fetch_rejects_invalid_original_domain_before_http():
    adapter, session = _adapter_with(FakeResponse())
    with pytest.raises(InvalidCoupangURLError):
        adapter.fetch("https://evil.example.com/vp/products/1")
    assert session.calls == []  # no HTTP request was made


def test_fetch_rejects_non_https():
    adapter, session = _adapter_with(FakeResponse())
    with pytest.raises(InvalidCoupangURLError):
        adapter.fetch("http://www.coupang.com/vp/products/1")
    assert session.calls == []


def test_fetch_http_error_rejected():
    adapter, _ = _adapter_with(FakeResponse(status_code=503, url=DIRECT_URL))
    with pytest.raises(CoupangHTTPError):
        adapter.fetch(DIRECT_URL)


def test_fetch_timeout_converted():
    adapter, _ = _adapter_with(exc=TimeoutError("slow"))
    with pytest.raises(CoupangTimeoutError):
        adapter.fetch(DIRECT_URL)


def test_fetch_connection_error_converted():
    adapter, _ = _adapter_with(exc=ConnectionError("refused"))
    with pytest.raises(CoupangConnectionError):
        adapter.fetch(DIRECT_URL)


def test_fetch_redirect_to_external_domain_rejected():
    adapter, _ = _adapter_with(FakeResponse(url="https://evil.example.com/vp/products/1"))
    with pytest.raises(InvalidRedirectError):
        adapter.fetch(AFFILIATE_URL)


def test_fetch_redirect_to_non_product_page_rejected():
    adapter, _ = _adapter_with(FakeResponse(url="https://www.coupang.com/np/categories/1"))
    with pytest.raises(InvalidRedirectError):
        adapter.fetch(AFFILIATE_URL)


def test_fetch_empty_response_rejected():
    adapter, _ = _adapter_with(FakeResponse(url=DIRECT_URL, text="   "))
    with pytest.raises(EmptyResponseError):
        adapter.fetch(DIRECT_URL)


def test_fetch_non_html_response_rejected():
    adapter, _ = _adapter_with(
        FakeResponse(url=DIRECT_URL, text='{"a": 1}', content_type="application/json")
    )
    with pytest.raises(NonHtmlResponseError):
        adapter.fetch(DIRECT_URL)


def test_fetch_does_not_alter_affiliate_url():
    adapter, _ = _adapter_with(FakeResponse(url=DIRECT_URL))
    adapter.fetch(AFFILIATE_URL)
    # Original affiliate URL preserved; final redirected URL is internal metadata.
    assert adapter._url == AFFILIATE_URL
    assert adapter._final_url == DIRECT_URL
