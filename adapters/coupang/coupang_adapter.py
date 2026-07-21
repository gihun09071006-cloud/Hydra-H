"""Coupang marketplace adapter.

Fetches raw Coupang product-page HTML over HTTP for the existing
:class:`ProductParser`. It accepts Coupang Partners affiliate URLs and direct
Coupang product URLs; affiliate URLs are resolved by following normal HTTP
redirects.

Boundary: :meth:`fetch` only retrieves *validated raw HTML*. It never parses
product fields, builds ProductFacts, calls an LLM, contains marketing or
affiliate-publishing logic, or alters the original affiliate URL. The original
affiliate URL remains the external publishing link; the final redirected URL is
internal product-analysis metadata only.

The legacy :meth:`load` / :meth:`extract` / :meth:`to_product_intelligence`
placeholder path is retained for backward compatibility.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from adapters.base.product_adapter import ProductAdapter

try:  # HTTP client is optional at import time; the default session needs it.
    import requests as _requests
    from requests import exceptions as _rexc
except ImportError:  # pragma: no cover - requests is available in this project
    _requests = None
    _rexc = None

# Exceptions raised from client.get() mapped to descriptive adapter errors.
_TIMEOUT_EXCEPTIONS: tuple[type[BaseException], ...] = (TimeoutError,)
_CONNECTION_EXCEPTIONS: tuple[type[BaseException], ...] = (ConnectionError, OSError)
if _rexc is not None:
    _TIMEOUT_EXCEPTIONS = _TIMEOUT_EXCEPTIONS + (_rexc.Timeout,)
    _CONNECTION_EXCEPTIONS = _CONNECTION_EXCEPTIONS + (_rexc.ConnectionError, _rexc.RequestException)


class CoupangFetchError(Exception):
    """Base class for Coupang adapter fetch failures."""


class InvalidCoupangURLError(CoupangFetchError, ValueError):
    """The requested URL is not a valid/allowed Coupang URL."""


class InvalidRedirectError(CoupangFetchError, ValueError):
    """A redirect ended on an invalid (external or non-product) destination."""


class CoupangHTTPError(CoupangFetchError):
    """The server returned an error HTTP status."""


class CoupangTimeoutError(CoupangFetchError):
    """The request timed out."""


class CoupangConnectionError(CoupangFetchError):
    """The request failed to connect."""


class NonHtmlResponseError(CoupangFetchError):
    """The response was not HTML."""


class EmptyResponseError(CoupangFetchError):
    """The response body was empty."""


class CoupangAdapter(ProductAdapter):
    """Adapter for Coupang product listings."""

    marketplace = "Coupang"

    #: Hosts recognized as Coupang.
    _COUPANG_HOST_SUFFIX = "coupang.com"

    #: Host used by Coupang affiliate (short) links.
    _AFFILIATE_HOST = "link.coupang.com"

    #: The only hosts this adapter may request (SSRF guard).
    _ALLOWED_HOSTS = frozenset({"link.coupang.com", "www.coupang.com", "coupang.com"})

    #: Explicit request timeout in seconds.
    _TIMEOUT = 10.0

    #: Browser-like request headers.
    _HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    def __init__(self, http_client: Any = None) -> None:
        # An injectable/mockable HTTP session exposing ``get(url, headers,
        # timeout, allow_redirects)``. Defaults to a requests.Session lazily.
        self._http_client = http_client
        self._url: str | None = None
        self._final_url: str | None = None
        self._raw: dict[str, Any] | None = None
        self._extracted: dict[str, Any] | None = None

    # -- HTTP fetching -----------------------------------------------------

    def fetch(self, url: str) -> str:
        """Fetch and return the raw Coupang product-page HTML for ``url``.

        Accepts a direct Coupang product URL or an affiliate link. Affiliate
        links are resolved by following normal HTTP redirects. Both the original
        URL and the final redirected URL are validated. Returns raw HTML only.
        """
        self._validate_request_url(url)

        client = self._client()
        try:
            response = client.get(
                url.strip(),
                headers=dict(self._HEADERS),
                timeout=self._TIMEOUT,
                allow_redirects=True,
            )
        except _TIMEOUT_EXCEPTIONS as exc:
            raise CoupangTimeoutError(f"Timed out fetching Coupang URL: {url}") from exc
        except _CONNECTION_EXCEPTIONS as exc:
            raise CoupangConnectionError(f"Connection failed fetching Coupang URL: {url}") from exc

        self._validate_status(response, url)

        final_url = str(getattr(response, "url", "") or "")
        self._validate_final_product_url(final_url)

        body = str(getattr(response, "text", "") or "")
        self._validate_html(response, body)

        # Keep the ORIGINAL url (external publishing link); the final redirected
        # url is internal product-analysis metadata only.
        self._url = url
        self._final_url = final_url
        return body

    def validate_source_url(self, url: str) -> None:
        """Validate a source URL as a Coupang affiliate or product URL.

        Used by local-HTML mode, where the URL is recorded as source metadata
        rather than fetched. Reuses the same strict validation as :meth:`fetch`
        (no weakening). Raises :class:`InvalidCoupangURLError` if invalid.
        """
        self._validate_request_url(url)

    def _client(self) -> Any:
        if self._http_client is None:
            if _requests is None:  # pragma: no cover - requests is present here
                raise RuntimeError(
                    "No HTTP client available; install 'requests' or inject http_client"
                )
            self._http_client = _requests.Session()
        return self._http_client

    def _validate_request_url(self, url: str) -> None:
        if not isinstance(url, str) or not url.strip():
            raise InvalidCoupangURLError("URL must be a non-empty string")
        parsed = urlparse(url.strip())
        if parsed.scheme != "https":
            raise InvalidCoupangURLError(f"URL must use HTTPS: {url}")
        host = (parsed.hostname or "").lower()
        if host not in self._ALLOWED_HOSTS:
            raise InvalidCoupangURLError(f"Non-Coupang host: {host or url!r}")
        if host == self._AFFILIATE_HOST:
            return  # affiliate link — resolved by following redirects
        if "products" not in parsed.path:
            raise InvalidCoupangURLError(f"Not a Coupang product URL: {url}")

    def _validate_final_product_url(self, final_url: str) -> None:
        if not final_url:
            raise InvalidRedirectError("No final URL after following redirects")
        parsed = urlparse(final_url)
        if parsed.scheme != "https":
            raise InvalidRedirectError(f"Final URL is not HTTPS: {final_url}")
        host = (parsed.hostname or "").lower()
        if host not in self._ALLOWED_HOSTS:
            raise InvalidRedirectError(f"Redirect ended on an external domain: {host}")
        if host == self._AFFILIATE_HOST or "products" not in parsed.path:
            raise InvalidRedirectError(
                f"Redirect did not end on a Coupang product page: {final_url}"
            )

    @staticmethod
    def _validate_status(response: Any, url: str) -> None:
        # Equivalent to requests' raise_for_status(), but client-agnostic.
        status = getattr(response, "status_code", None)
        if status is not None and int(status) >= 400:
            raise CoupangHTTPError(f"HTTP {status} fetching Coupang URL: {url}")

    @staticmethod
    def _validate_html(response: Any, body: str) -> None:
        if not body or not body.strip():
            raise EmptyResponseError("Empty response body from Coupang")
        headers = getattr(response, "headers", {}) or {}
        content_type = ""
        try:
            content_type = headers.get("Content-Type") or headers.get("content-type") or ""
        except AttributeError:
            for key, value in dict(headers).items():
                if str(key).lower() == "content-type":
                    content_type = value
                    break
        if "html" not in str(content_type).lower():
            raise NonHtmlResponseError(f"Response is not HTML (Content-Type: {content_type!r})")

    # -- ProductAdapter interface ------------------------------------------

    def validate(self, url: str) -> bool:
        """Return ``True`` for a well-formed Coupang product URL."""
        if not isinstance(url, str) or not url.strip():
            return False
        parsed = urlparse(url.strip())
        if parsed.scheme not in ("http", "https"):
            return False
        host = parsed.netloc.lower()
        if not (host == self._COUPANG_HOST_SUFFIX or host.endswith("." + self._COUPANG_HOST_SUFFIX)):
            return False
        # Coupang product URLs point at a product listing path.
        return "products" in parsed.path

    def is_affiliate_url(self, url: str) -> bool:
        """Return ``True`` for a Coupang affiliate (short) link."""
        if not isinstance(url, str) or not url.strip():
            return False
        parsed = urlparse(url.strip())
        if parsed.scheme not in ("http", "https"):
            return False
        return parsed.netloc.lower() == self._AFFILIATE_HOST

    def load(self, url: str) -> dict[str, Any]:
        """Return mock source data for ``url``.

        No network, browser, or API access is performed. The shape mimics what a
        real loader would return once implemented.
        """
        self._url = url
        self._raw = {
            "source_url": url,
            "listing": {
                "title": "Cordless Neck & Shoulder Massager",
                "brand": "RelaxPro",
                "category": "Health & Wellness",
                "price": 39900,
                "currency": "KRW",
                "country": "South Korea",
                "bullet_points": [
                    "Cordless, wearable design",
                    "Heat therapy",
                    "Adjustable intensity",
                    "Improves circulation",
                    "Warms tight muscles",
                ],
            },
        }
        return self._raw

    def extract(self) -> dict[str, Any]:
        """Flatten the loaded mock source into intermediate fields."""
        if self._raw is None:
            raise RuntimeError("load() must be called before extract()")
        listing = self._raw["listing"]
        self._extracted = {
            "name": listing["title"],
            "brand": listing["brand"],
            "category": listing["category"],
            "price": listing["price"],
            "currency": listing["currency"],
            "country": listing["country"],
            "features": list(listing["bullet_points"]),
        }
        return self._extracted

    def to_product_intelligence(self) -> dict[str, Any]:
        """Assemble a Product Intelligence Record from the extracted fields.

        The result validates against
        ``data/schemas/product_intelligence.schema.json``.
        """
        if self._extracted is None:
            raise RuntimeError("extract() must be called before to_product_intelligence()")
        e = self._extracted
        return {
            "product_identity": {
                "product_name": e["name"],
                "brand": e["brand"],
                "category": e["category"],
                "price": {
                    "amount": e["price"],
                    "currency": e["currency"],
                },
                "country": e["country"],
                "marketplace": self.marketplace,
            },
            "functional_analysis": {
                "primary_function": "Relieves neck and shoulder tension",
                "secondary_functions": [
                    "Improves circulation",
                    "Warms tight muscles",
                ],
                "top_features": [
                    "Cordless wearable design",
                    "Heat therapy",
                    "Adjustable intensity",
                ],
                "usp": "Deep-kneading massage with heat in a cordless, wearable design",
            },
            "visual_analysis": {
                "benefit_visually_demonstrable": True,
                "visual_proof_strength": 82,
                "before_after_possible": True,
                "transformation_possible": False,
            },
            "customer_analysis": {
                "primary_target": "Office workers 25-45 with neck and shoulder tension",
                "secondary_target": "Older adults with muscle stiffness",
                "buying_situation": "After long hours at a desk or screen",
                "daily_usage": "10-15 minutes in the evening",
                "emotional_motivation": "Relief and relaxation after a stressful day",
                "functional_motivation": "Reduce chronic neck and shoulder pain",
            },
            "pain_analysis": [
                {
                    "problem": "Chronic neck and shoulder tension from desk work",
                    "severity": 80,
                    "rank": 1,
                },
                {
                    "problem": "Limited time or budget for regular massage therapy",
                    "severity": 60,
                    "rank": 2,
                },
            ],
            "objection_analysis": [
                {
                    "objection": "Unsure whether the massage is strong enough to help",
                    "probability": 60,
                    "rank": 1,
                },
                {
                    "objection": "Concerned about battery life and durability",
                    "probability": 45,
                    "rank": 2,
                },
            ],
            "competitive_analysis": {
                "existing_alternatives": [
                    "Manual massage tools",
                    "Corded massage cushions",
                ],
                "offline_alternative": "Professional massage therapy",
                "diy_alternative": "Self-massage and stretching",
                "why_buy_this_instead": (
                    "Delivers professional-style deep kneading with heat, cordless and on demand"
                ),
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
                "reason": (
                    "Satisfying, visually demonstrable relief content suits short vertical "
                    "video; the high satisfaction potential fits Instagram Reels."
                ),
            },
        }
