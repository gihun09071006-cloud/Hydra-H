"""Product Intelligence Parser for HYDRA.

Converts a raw HTML string into a valid Product Intelligence object
(``data/schemas/product_intelligence.schema.json``). Uses HTML parsing only —
no Selenium, Playwright, browser automation, external APIs, or network requests.

Extraction honors two rules:

* **Never fabricate values.** :meth:`ProductParser.extract` returns ``None`` (or
  an empty list) for anything it cannot find in the HTML.
* **Use the existing schema.** :meth:`ProductParser.to_product_intelligence`
  maps the extracted values onto the canonical Product Intelligence schema. The
  schema requires analytic sections a parser cannot derive from a listing
  (virality, platform, pain, etc.); those are filled with neutral placeholders
  (empty strings, ``0`` scores, empty arrays) — never invented product facts —
  so the object validates and the Product Intelligence Engine can fill them
  later. ``top_features`` must contain exactly three entries, so it is padded
  with empty strings when fewer are found.
"""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from typing import Any

_JSON_LD_RE = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)


class _ListingHTMLParser(HTMLParser):
    """Collects meta tags, feature list items, and the seller name."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.metas: dict[str, str] = {}
        self.features: list[str] = []
        self.seller: str | None = None
        self._capture: str | None = None
        self._buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v or "") for k, v in attrs}
        if tag == "meta":
            key = a.get("property") or a.get("name")
            if key and "content" in a:
                self.metas[key] = a["content"]
            return
        classes = a.get("class", "").split()
        if tag == "li" and "prod-feature" in classes:
            self._capture, self._buf = "feature", []
        elif "seller-name" in classes:
            self._capture, self._buf = "seller", []

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._buf.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._capture == "feature" and tag == "li":
            text = "".join(self._buf).strip()
            if text:
                self.features.append(text)
            self._capture, self._buf = None, []
        elif self._capture == "seller":
            text = "".join(self._buf).strip()
            if text:
                self.seller = text
            self._capture, self._buf = None, []


def _iter_ld(data: Any):
    if isinstance(data, list):
        for item in data:
            yield from _iter_ld(item)
    elif isinstance(data, dict):
        graph = data.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                yield from _iter_ld(item)
        yield data


def _is_product(obj: dict[str, Any]) -> bool:
    t = obj.get("@type")
    if isinstance(t, list):
        return any(str(x).endswith("Product") for x in t)
    return isinstance(t, str) and t.endswith("Product")


def _json_ld_product(html: str) -> dict[str, Any]:
    for match in _JSON_LD_RE.finditer(html):
        try:
            data = json.loads(match.group(1).strip())
        except (ValueError, TypeError):
            continue
        for obj in _iter_ld(data):
            if _is_product(obj):
                return obj
    return {}


def _first(value: Any) -> Any:
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _parse_price(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = re.sub(r"[^0-9.]", "", str(value))
    if not cleaned or cleaned == ".":
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _text_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


class ProductParser:
    """Parses raw HTML into a Product Intelligence object."""

    def extract(self, html: str) -> dict[str, Any]:
        """Extract listing fields from ``html``.

        Returns a dict with ``None`` / ``[]`` for anything not present. Never
        fabricates a value.
        """
        html = html or ""
        listing = _ListingHTMLParser()
        try:
            listing.feed(html)
            listing.close()
        except Exception:  # noqa: BLE001 - malformed HTML must not raise
            pass
        metas = listing.metas

        product = _json_ld_product(html)
        offer = product.get("offers")
        if isinstance(offer, list):
            offer = offer[0] if offer else {}
        if not isinstance(offer, dict):
            offer = {}

        brand = product.get("brand")
        if isinstance(brand, dict):
            brand = brand.get("name")

        name = product.get("name") or metas.get("og:title")
        image = _first(product.get("image")) or metas.get("og:image")
        description = product.get("description") or metas.get("og:description")
        price = _parse_price(offer.get("price") or metas.get("product:price:amount"))
        currency = offer.get("priceCurrency") or metas.get("product:price:currency")

        return {
            "product_name": _text_or_none(name),
            "brand": _text_or_none(brand),
            "price": price,
            "currency": _text_or_none(currency),
            "category": _text_or_none(product.get("category")),
            "main_image_url": _text_or_none(image),
            "description": _text_or_none(description),
            "features": list(listing.features),
            "seller_name": _text_or_none(listing.seller),
        }

    def to_product_intelligence(
        self,
        extracted: dict[str, Any],
        *,
        marketplace: str = "",
        country: str = "",
    ) -> dict[str, Any]:
        """Map extracted values onto the Product Intelligence schema.

        Non-extractable required fields are filled with neutral placeholders
        (never fabricated product facts). ``top_features`` is padded to exactly
        three entries with empty strings.
        """
        features = [f for f in extracted.get("features") or [] if f]
        top_features = (features[:3] + ["", "", ""])[:3]

        return {
            "product_identity": {
                "product_name": extracted.get("product_name") or "",
                "brand": extracted.get("brand") or "",
                "category": extracted.get("category") or "",
                "price": {
                    "amount": extracted.get("price") if extracted.get("price") is not None else 0,
                    "currency": extracted.get("currency") or "",
                },
                "country": country,
                "marketplace": marketplace,
            },
            "functional_analysis": {
                "primary_function": "",
                "secondary_functions": [],
                "top_features": top_features,
                "usp": "",
            },
            "visual_analysis": {
                "benefit_visually_demonstrable": False,
                "visual_proof_strength": 0,
                "before_after_possible": False,
                "transformation_possible": False,
            },
            "customer_analysis": {
                "primary_target": "",
                "secondary_target": "",
                "buying_situation": "",
                "daily_usage": "",
                "emotional_motivation": "",
                "functional_motivation": "",
            },
            "pain_analysis": [],
            "objection_analysis": [],
            "competitive_analysis": {
                "existing_alternatives": [],
                "offline_alternative": "",
                "diy_alternative": "",
                "why_buy_this_instead": "",
            },
            "virality_analysis": {
                "scroll_stop_potential": 0,
                "surprise_potential": 0,
                "satisfaction_potential": 0,
                "shareability": 0,
                "comment_potential": 0,
            },
            "platform_recommendation": {
                "primary_platform": "Instagram Reels",
                "reason": "",
            },
        }

    def parse(self, html: str, *, marketplace: str = "", country: str = "") -> dict[str, Any]:
        """Convenience: ``extract`` then ``to_product_intelligence``."""
        return self.to_product_intelligence(
            self.extract(html), marketplace=marketplace, country=country
        )
