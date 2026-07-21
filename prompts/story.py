"""Story prompt builder (pure function).

Input: CreativeStrategy contract. Output contract: Storyboard.
"""

from __future__ import annotations

import json

from contracts.creative_strategy import CreativeStrategy
from prompts._rules import JSON_OUTPUT_RULES

SYSTEM_PROMPT = (
    "You are HYDRA's Story Engine. Turn a creative strategy into a vertical, "
    "short-form video storyboard. Prefer roughly 15-25 seconds total. Use a "
    "scene-based structure where each scene has one clear communication objective, "
    "maintain continuity between scenes, and include Hook, Problem/Desire, Product "
    "Reveal, Demonstration/Proof, and Call To Action when appropriate. Do not require "
    "copyrighted celebrities or trademarked characters."
)

_REQUIRED_SHAPE = """{
  "story_pattern": "",
  "duration": 20,
  "scenes": [
    {"scene": 1, "duration": 3, "goal": "Hook", "description": ""}
  ]
}"""


def build_story_prompt(creative_strategy: CreativeStrategy) -> str:
    """Return the user prompt for storyboard generation."""
    strategy_json = json.dumps(creative_strategy.to_dict(), ensure_ascii=False, indent=2)
    return (
        "Design a vertical short-form video storyboard from this creative strategy.\n\n"
        "Reasoning goals:\n"
        "- Prefer ~15-25 seconds total; scene durations must sum to `duration`.\n"
        "- Each scene has one clear communication objective in `goal`.\n"
        "- Maintain continuity between scenes.\n"
        "- Cover Hook, Problem/Desire, Product Reveal, Demonstration/Proof, and CTA "
        "when appropriate.\n"
        "- `scene` and `duration` are integers; `goal` and `description` are strings.\n\n"
        f"CREATIVE STRATEGY (JSON):\n{strategy_json}\n\n"
        f"Return JSON with exactly this shape and keys:\n{_REQUIRED_SHAPE}\n\n"
        f"{JSON_OUTPUT_RULES}"
    )
