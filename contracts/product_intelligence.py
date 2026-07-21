"""ProductIntelligence contract — AI-enriched product understanding.

Data only. Strongly typed mirror of the Product Intelligence contract that
Engines and Providers exchange, so a Provider never returns an arbitrary dict.
Field names match the canonical structure exactly.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Price:
    amount: float = 0
    currency: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Price":
        data = data or {}
        return cls(amount=data.get("amount", 0), currency=data.get("currency", ""))


@dataclass
class ProductIdentity:
    product_name: str = ""
    brand: str = ""
    category: str = ""
    price: Price = field(default_factory=Price)
    country: str = ""
    marketplace: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProductIdentity":
        data = data or {}
        return cls(
            product_name=data.get("product_name", ""),
            brand=data.get("brand", ""),
            category=data.get("category", ""),
            price=Price.from_dict(data.get("price", {})),
            country=data.get("country", ""),
            marketplace=data.get("marketplace", ""),
        )


@dataclass
class FunctionalAnalysis:
    primary_function: str = ""
    secondary_functions: list[str] = field(default_factory=list)
    top_features: list[str] = field(default_factory=list)
    usp: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FunctionalAnalysis":
        data = data or {}
        return cls(
            primary_function=data.get("primary_function", ""),
            secondary_functions=list(data.get("secondary_functions") or []),
            top_features=list(data.get("top_features") or []),
            usp=data.get("usp", ""),
        )


@dataclass
class VisualAnalysis:
    benefit_visually_demonstrable: bool = False
    visual_proof_strength: int = 0
    before_after_possible: bool = False
    transformation_possible: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VisualAnalysis":
        data = data or {}
        return cls(
            benefit_visually_demonstrable=data.get("benefit_visually_demonstrable", False),
            visual_proof_strength=data.get("visual_proof_strength", 0),
            before_after_possible=data.get("before_after_possible", False),
            transformation_possible=data.get("transformation_possible", False),
        )


@dataclass
class CustomerAnalysis:
    primary_target: str = ""
    secondary_target: str = ""
    buying_situation: str = ""
    daily_usage: str = ""
    emotional_motivation: str = ""
    functional_motivation: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CustomerAnalysis":
        data = data or {}
        return cls(
            primary_target=data.get("primary_target", ""),
            secondary_target=data.get("secondary_target", ""),
            buying_situation=data.get("buying_situation", ""),
            daily_usage=data.get("daily_usage", ""),
            emotional_motivation=data.get("emotional_motivation", ""),
            functional_motivation=data.get("functional_motivation", ""),
        )


@dataclass
class Pain:
    problem: str = ""
    severity: int = 0
    rank: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Pain":
        data = data or {}
        return cls(
            problem=data.get("problem", ""),
            severity=data.get("severity", 0),
            rank=data.get("rank", 0),
        )


@dataclass
class Objection:
    objection: str = ""
    probability: int = 0
    rank: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Objection":
        data = data or {}
        return cls(
            objection=data.get("objection", ""),
            probability=data.get("probability", 0),
            rank=data.get("rank", 0),
        )


@dataclass
class CompetitiveAnalysis:
    existing_alternatives: list[str] = field(default_factory=list)
    offline_alternative: str = ""
    diy_alternative: str = ""
    why_buy_this_instead: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CompetitiveAnalysis":
        data = data or {}
        return cls(
            existing_alternatives=list(data.get("existing_alternatives") or []),
            offline_alternative=data.get("offline_alternative", ""),
            diy_alternative=data.get("diy_alternative", ""),
            why_buy_this_instead=data.get("why_buy_this_instead", ""),
        )


@dataclass
class ViralityAnalysis:
    scroll_stop_potential: int = 0
    surprise_potential: int = 0
    satisfaction_potential: int = 0
    shareability: int = 0
    comment_potential: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ViralityAnalysis":
        data = data or {}
        return cls(
            scroll_stop_potential=data.get("scroll_stop_potential", 0),
            surprise_potential=data.get("surprise_potential", 0),
            satisfaction_potential=data.get("satisfaction_potential", 0),
            shareability=data.get("shareability", 0),
            comment_potential=data.get("comment_potential", 0),
        )


@dataclass
class PlatformRecommendation:
    primary_platform: str = ""
    reason: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlatformRecommendation":
        data = data or {}
        return cls(
            primary_platform=data.get("primary_platform", ""),
            reason=data.get("reason", ""),
        )


@dataclass
class ProductIntelligence:
    product_identity: ProductIdentity = field(default_factory=ProductIdentity)
    functional_analysis: FunctionalAnalysis = field(default_factory=FunctionalAnalysis)
    visual_analysis: VisualAnalysis = field(default_factory=VisualAnalysis)
    customer_analysis: CustomerAnalysis = field(default_factory=CustomerAnalysis)
    pain_analysis: list[Pain] = field(default_factory=list)
    objection_analysis: list[Objection] = field(default_factory=list)
    competitive_analysis: CompetitiveAnalysis = field(default_factory=CompetitiveAnalysis)
    virality_analysis: ViralityAnalysis = field(default_factory=ViralityAnalysis)
    platform_recommendation: PlatformRecommendation = field(default_factory=PlatformRecommendation)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProductIntelligence":
        data = data or {}
        return cls(
            product_identity=ProductIdentity.from_dict(data.get("product_identity", {})),
            functional_analysis=FunctionalAnalysis.from_dict(data.get("functional_analysis", {})),
            visual_analysis=VisualAnalysis.from_dict(data.get("visual_analysis", {})),
            customer_analysis=CustomerAnalysis.from_dict(data.get("customer_analysis", {})),
            pain_analysis=[Pain.from_dict(p) for p in data.get("pain_analysis") or []],
            objection_analysis=[Objection.from_dict(o) for o in data.get("objection_analysis") or []],
            competitive_analysis=CompetitiveAnalysis.from_dict(data.get("competitive_analysis", {})),
            virality_analysis=ViralityAnalysis.from_dict(data.get("virality_analysis", {})),
            platform_recommendation=PlatformRecommendation.from_dict(
                data.get("platform_recommendation", {})
            ),
        )
