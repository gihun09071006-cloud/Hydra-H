"""Coupang marketplace adapter (placeholder).

This is HYDRA's first executable marketplace adapter. It validates Coupang
product URLs and returns a Product Intelligence Record that conforms to
``data/schemas/product_intelligence.schema.json``.

Placeholder scope (by design):
    * No web scraping.
    * No browser automation.
    * No external API calls.

Instead, :meth:`load` returns mock source data. The real data-acquisition
strategy will replace :meth:`load`/:meth:`extract` in a future milestone without
changing the :class:`ProductAdapter` interface or any downstream engine.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from adapters.base.product_adapter import ProductAdapter


class CoupangAdapter(ProductAdapter):
    """Adapter for Coupang product listings."""

    marketplace = "Coupang"

    #: Hosts recognized as Coupang.
    _COUPANG_HOST_SUFFIX = "coupang.com"

    #: Host used by Coupang affiliate (short) links.
    _AFFILIATE_HOST = "link.coupang.com"

    #: Mock product-listing HTML returned by ``fetch`` (placeholder — no network).
    _MOCK_HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta property="og:title" content="Cordless Neck &amp; Shoulder Massager">
  <meta property="og:image" content="https://image.coupang.com/products/massager-main.jpg">
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": "Cordless Neck & Shoulder Massager",
    "brand": {"@type": "Brand", "name": "RelaxPro"},
    "category": "Health & Wellness",
    "image": "https://image.coupang.com/products/massager-main.jpg",
    "description": "Deep-kneading cordless massager with heat therapy for neck and shoulders.",
    "offers": {"@type": "Offer", "price": "39900", "priceCurrency": "KRW"}
  }
  </script>
</head>
<body>
  <span class="seller-name">RelaxPro Official Store</span>
  <ul class="feature-list">
    <li class="prod-feature">Cordless wearable design</li>
    <li class="prod-feature">Heat therapy</li>
    <li class="prod-feature">Adjustable intensity</li>
  </ul>
</body>
</html>"""

    def __init__(self) -> None:
        self._url: str | None = None
        self._raw: dict[str, Any] | None = None
        self._extracted: dict[str, Any] | None = None

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

    def fetch(self, url: str) -> str:
        """Return the raw product HTML for ``url``.

        Accepts a direct Coupang product URL or an affiliate link. For affiliate
        links the adapter is responsible for following the redirect to the
        product page — here a placeholder that performs no network access and
        returns mock HTML. Raises :class:`ValueError` for non-Coupang URLs.
        """
        if self.is_affiliate_url(url) or self.validate(url):
            self._url = url
            return self._MOCK_HTML
        raise ValueError(f"Invalid Coupang URL: {url}")

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
