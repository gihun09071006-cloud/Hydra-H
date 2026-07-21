"""Creative Strategy prompt builder (pure function).

Input: ProductIntelligence contract (+ optional Market Fit result).
Output contract: CreativeStrategy.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from contracts.product_intelligence import ProductIntelligence
from prompts._rules import JSON_OUTPUT_RULES

SYSTEM_PROMPT = (
    "You are HYDRA's Creative Strategy Engine. Choose the single best advertising "
    "strategy for a product from its Product Intelligence (and Market Fit result, "
    "when supplied). Select one primary angle, a target emotion, a strong opening "
    "hook, a proof/demonstration approach, and a call-to-action direction. Use the "
    "Market Fit information when it is provided. Do not fabricate discounts, scarcity, "
    "medical claims, guarantees, or reviews."
)

_REQUIRED_SHAPE = """{
  "strategy": "",
  "reason": "",
  "confidence": 0,
  "hook_type": "",
  "story_pattern": "",
  "cta_style": ""
}"""


def build_creative_strategy_prompt(
    product_intelligence: ProductIntelligence,
    market_fit_result: Optional[dict[str, Any]] = None,
) -> str:
    """Return the user prompt for creative strategy selection."""
    pi_json = json.dumps(product_intelligence.to_dict(), ensure_ascii=False, indent=2)
    mf_json = json.dumps(market_fit_result or {}, ensure_ascii=False, indent=2)
    return (
        "Select the single best advertising strategy for this product.\n\n"
        "Reasoning goals:\n"
        "- Choose ONE primary advertising angle (the `strategy`).\n"
        "- Choose a target emotion and a strong opening `hook_type`.\n"
        "- Define the proof/demonstration approach and a `cta_style` direction.\n"
        "- Use the Market Fit result when it is non-empty.\n"
        "- `confidence` is an integer 0-100.\n\n"
        f"PRODUCT INTELLIGENCE (JSON):\n{pi_json}\n\n"
        f"MARKET FIT RESULT (JSON, may be empty):\n{mf_json}\n\n"
        f"Return JSON with exactly this shape and keys:\n{_REQUIRED_SHAPE}\n\n"
        f"{JSON_OUTPUT_RULES}"
    )
