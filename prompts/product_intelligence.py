"""Product Intelligence prompt builder (pure function).

Input: ProductFacts contract. Output contract: ProductIntelligence.
"""

from __future__ import annotations

import json

from contracts.product_facts import ProductFacts
from prompts._rules import JSON_OUTPUT_RULES

SYSTEM_PROMPT = (
    "You are HYDRA's Product Intelligence Engine. Analyze a product from its raw "
    "facts and return a structured Product Intelligence Record. Distinguish product "
    "features from customer outcomes, identify likely customer segments, and surface "
    "pains, desires, objections, and purchase triggers. Preserve uncertainty when the "
    "source data is incomplete and avoid unsupported factual claims."
)

_REQUIRED_SHAPE = """{
  "product_identity": {"product_name": "", "brand": "", "category": "",
    "price": {"amount": 0, "currency": ""}, "country": "", "marketplace": ""},
  "functional_analysis": {"primary_function": "", "secondary_functions": [],
    "top_features": ["", "", ""], "usp": ""},
  "visual_analysis": {"benefit_visually_demonstrable": false,
    "visual_proof_strength": 0, "before_after_possible": false,
    "transformation_possible": false},
  "customer_analysis": {"primary_target": "", "secondary_target": "",
    "buying_situation": "", "daily_usage": "", "emotional_motivation": "",
    "functional_motivation": ""},
  "pain_analysis": [{"problem": "", "severity": 0, "rank": 1}],
  "objection_analysis": [{"objection": "", "probability": 0, "rank": 1}],
  "competitive_analysis": {"existing_alternatives": [], "offline_alternative": "",
    "diy_alternative": "", "why_buy_this_instead": ""},
  "virality_analysis": {"scroll_stop_potential": 0, "surprise_potential": 0,
    "satisfaction_potential": 0, "shareability": 0, "comment_potential": 0},
  "platform_recommendation": {"primary_platform": "Instagram Reels", "reason": ""}
}"""


def build_product_intelligence_prompt(product_facts: ProductFacts) -> str:
    """Return the user prompt for product intelligence analysis."""
    facts_json = json.dumps(product_facts.to_dict(), ensure_ascii=False, indent=2)
    return (
        "Analyze the following product and produce a Product Intelligence Record.\n\n"
        "Reasoning goals:\n"
        "- Separate concrete features from the customer outcomes they enable.\n"
        "- Identify the primary and secondary customer segments.\n"
        "- Rank pains by severity and objections by probability (rank 1 = strongest).\n"
        "- Judge whether the benefit is visually demonstrable.\n"
        "- Score all 0-100 fields as integers; use exactly three top_features.\n"
        "- primary_platform must be one of: Instagram Reels, TikTok, YouTube Shorts.\n\n"
        f"PRODUCT FACTS (JSON):\n{facts_json}\n\n"
        f"Return JSON with exactly this shape and keys:\n{_REQUIRED_SHAPE}\n\n"
        f"{JSON_OUTPUT_RULES}"
    )
