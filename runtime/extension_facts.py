"""Map browser-extension JSON output into the existing ProductFacts contract.

The Coupang browser extension exports a normalized product JSON captured from a
rendered page. This module validates and maps it onto the single ProductFacts
contract — it never defines a second contract. Data mapping only; no networking.
"""

from __future__ import annotations

from typing import Any

from contracts.product_facts import ProductFacts

_SUPPORTED_MARKETPLACES = {"coupang"}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def product_facts_from_extension(data: Any) -> ProductFacts:
    """Validate and map extension JSON into a :class:`ProductFacts`.

    Raises :class:`ValueError` with a concise message on invalid input.
    """
    if not isinstance(data, dict):
        raise ValueError("extension JSON must be a JSON object")

    marketplace = data.get("marketplace")
    if marketplace is not None and str(marketplace).lower() not in _SUPPORTED_MARKETPLACES:
        raise ValueError(f"unsupported marketplace: {marketplace!r}")

    product_name = data.get("product_name")
    if not product_name or not str(product_name).strip():
        raise ValueError("product_name is required")

    product_url = data.get("product_url")
    if not product_url or not str(product_url).strip():
        raise ValueError("product_url is required")

    price = data.get("price")
    if price is not None and not _is_number(price):
        raise ValueError("price must be a number or null")

    image_urls = data.get("image_urls")
    if image_urls is None:
        image_urls = []
    if not isinstance(image_urls, list):
        raise ValueError("image_urls must be a list")

    features = data.get("features")
    if features is None:
        features = []
    if not isinstance(features, list):
        raise ValueError("features must be a list")

    rating = data.get("rating")
    review_count = data.get("review_count")

    try:
        return ProductFacts(
            product_name=str(product_name),
            price=float(price) if _is_number(price) else None,
            currency=data.get("currency"),
            description=data.get("description"),
            features=[str(f) for f in features],
            # seller -> seller_name
            seller_name=data.get("seller"),
            marketplace="coupang",
            # image_urls[0] -> main_image_url; the rest preserved in image_urls
            main_image_url=str(image_urls[0]) if image_urls else None,
            image_urls=[str(u) for u in image_urls],
            # product_url -> source_url; affiliate_url preserved separately
            source_url=str(product_url),
            affiliate_url=data.get("affiliate_url"),
            product_id=str(data["product_id"]) if data.get("product_id") else None,
            item_id=str(data["item_id"]) if data.get("item_id") else None,
            rating=float(rating) if _is_number(rating) else None,
            review_count=int(review_count) if _is_number(review_count) else None,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid ProductFacts conversion: {exc}") from exc
