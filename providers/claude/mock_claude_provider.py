"""Mock Claude provider (deterministic).

Implements the :class:`AIProvider` interface with **deterministic mock** responses
that match HYDRA's expected contracts. It never calls an external API, opens a
socket, reads an API key, or uses randomness. This is the provider returned in
``HYDRA_AI_MODE=mock`` (the default) so tests and local runs stay deterministic
and offline.
"""

from __future__ import annotations

from typing import Any

from providers.base.provider import AIProvider


class MockClaudeProvider(AIProvider):
    """Deterministic placeholder provider."""

    name = "claude"

    def analyze_product(self, product_facts: dict[str, Any]) -> dict[str, Any]:
        facts = product_facts or {}
        name = facts.get("product_name") or facts.get("name") or "Sample Product"
        brand = facts.get("brand") or "Sample Brand"
        category = facts.get("category") or "General"

        price = facts.get("price")
        if isinstance(price, dict):
            amount = price.get("amount", 0)
            currency = price.get("currency") or facts.get("currency") or "USD"
        else:
            amount = price if isinstance(price, (int, float)) else 0
            currency = facts.get("currency") or "USD"

        raw_features = [f for f in (facts.get("features") or []) if f]
        top_features = (raw_features[:3] + [
            "Primary feature", "Secondary feature", "Tertiary feature",
        ])[:3]

        return {
            "product_identity": {
                "product_name": name,
                "brand": brand,
                "category": category,
                "price": {"amount": amount, "currency": currency},
                "country": facts.get("country") or "United States",
                "marketplace": facts.get("marketplace") or "Coupang",
            },
            "functional_analysis": {
                "primary_function": "Solve the core problem",
                "secondary_functions": ["Supporting benefit"],
                "top_features": top_features,
                "usp": "The distinctive advantage of this product",
            },
            "visual_analysis": {
                "benefit_visually_demonstrable": True,
                "visual_proof_strength": 70,
                "before_after_possible": True,
                "transformation_possible": False,
            },
            "customer_analysis": {
                "primary_target": "Primary audience",
                "secondary_target": "Secondary audience",
                "buying_situation": "When the need arises",
                "daily_usage": "Regular use",
                "emotional_motivation": "Confidence and relief",
                "functional_motivation": "Get a practical result",
            },
            "pain_analysis": [
                {"problem": "The main problem it solves", "severity": 70, "rank": 1},
            ],
            "objection_analysis": [
                {"objection": "Uncertain it works as claimed", "probability": 50, "rank": 1},
            ],
            "competitive_analysis": {
                "existing_alternatives": ["Comparable product"],
                "offline_alternative": "An offline option",
                "diy_alternative": "A do-it-yourself option",
                "why_buy_this_instead": "A clearer, faster result",
            },
            "virality_analysis": {
                "scroll_stop_potential": 70,
                "surprise_potential": 60,
                "satisfaction_potential": 75,
                "shareability": 60,
                "comment_potential": 55,
            },
            "platform_recommendation": {
                "primary_platform": "Instagram Reels",
                "reason": "Fits short vertical, visually demonstrable content",
            },
        }

    def generate_creative_strategy(
        self,
        product_intelligence: dict[str, Any],
        market_fit_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "strategy": "Visual Demonstration",
            "reason": (
                "Deterministic placeholder: selected Visual Demonstration; other "
                "strategies deferred. Expected impact: relevance and clarity."
            ),
            "confidence": 80,
            "hook_type": "Demonstration",
            "story_pattern": "Problem → Solution",
            "cta_style": "Direct",
        }

    def generate_story(self, strategy: dict[str, Any]) -> dict[str, Any]:
        story_pattern = (strategy or {}).get("story_pattern") or "Problem → Solution"
        scenes = [
            {"scene": 1, "duration": 3, "goal": "Hook", "description": "Open with an attention-grabbing moment."},
            {"scene": 2, "duration": 4, "goal": "Problem", "description": "Show the problem the viewer relates to."},
            {"scene": 3, "duration": 7, "goal": "Solution", "description": "Introduce the product as the solution."},
            {"scene": 4, "duration": 4, "goal": "Proof", "description": "Demonstrate proof that it works."},
            {"scene": 5, "duration": 2, "goal": "CTA", "description": "Close with a clear call to action."},
        ]
        return {"story_pattern": story_pattern, "duration": 20, "scenes": scenes}

    def compile_prompt(self, story: dict[str, Any]) -> dict[str, Any]:
        duration = (story or {}).get("duration", 20)
        return {
            "target_backend": "Higgsfield",
            "prompt": "Deterministic placeholder prompt compiled from the storyboard.",
            "negative_prompt": "low quality, distorted, watermark, text artifacts",
            "metadata": {
                "duration": duration,
                "aspect_ratio": "9:16",
                "language": "en",
                "version": "1.0",
            },
        }
