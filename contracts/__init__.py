"""Internal AI contracts shared between HYDRA Engines and Providers.

Strongly typed dataclasses so Providers never return arbitrary dicts. Data only —
no business logic, parsing, scoring, or API calls; only ``to_dict`` / ``from_dict``
serialization.
"""

from contracts.creative_strategy import CreativeStrategy
from contracts.product_facts import ProductFacts
from contracts.product_intelligence import (
    CompetitiveAnalysis,
    CustomerAnalysis,
    FunctionalAnalysis,
    Objection,
    Pain,
    PlatformRecommendation,
    Price,
    ProductIdentity,
    ProductIntelligence,
    ViralityAnalysis,
    VisualAnalysis,
)
from contracts.render_prompt import RenderMetadata, RenderPrompt
from contracts.storyboard import Scene, Storyboard

__all__ = [
    "ProductFacts",
    "ProductIntelligence",
    "ProductIdentity",
    "Price",
    "FunctionalAnalysis",
    "VisualAnalysis",
    "CustomerAnalysis",
    "Pain",
    "Objection",
    "CompetitiveAnalysis",
    "ViralityAnalysis",
    "PlatformRecommendation",
    "CreativeStrategy",
    "Storyboard",
    "Scene",
    "RenderPrompt",
    "RenderMetadata",
]
