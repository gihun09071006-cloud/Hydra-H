"""ProductFacts contract — raw extracted product information.

Data only. This is what a marketplace adapter / parser extracts before any AI
enrichment. Missing values are ``None`` (or an empty list); nothing is fabricated.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class ProductFacts:
    product_name: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    category: Optional[str] = None
    main_image_url: Optional[str] = None
    description: Optional[str] = None
    features: list[str] = field(default_factory=list)
    seller_name: Optional[str] = None
    marketplace: Optional[str] = None
    country: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProductFacts":
        data = data or {}
        return cls(
            product_name=data.get("product_name"),
            brand=data.get("brand"),
            price=data.get("price"),
            currency=data.get("currency"),
            category=data.get("category"),
            main_image_url=data.get("main_image_url"),
            description=data.get("description"),
            features=list(data.get("features") or []),
            seller_name=data.get("seller_name"),
            marketplace=data.get("marketplace"),
            country=data.get("country"),
        )
