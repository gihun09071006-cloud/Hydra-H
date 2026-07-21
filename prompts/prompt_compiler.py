"""Prompt Compiler prompt builder (pure function).

Input: Storyboard contract. Output contract: RenderPrompt.
"""

from __future__ import annotations

import json

from contracts.storyboard import Storyboard
from prompts._rules import JSON_OUTPUT_RULES

SYSTEM_PROMPT = (
    "You are HYDRA's Prompt Compiler. Convert a storyboard into a production-ready "
    "vertical-video generation prompt. Preserve product identity and scene continuity. "
    "The prompt should cover camera, lighting, composition, motion, environment, "
    "subject action, pacing, and visual constraints, and you must produce a useful "
    "negative prompt. Store non-prompt production information in metadata. Keep "
    "publishing captions and affiliate disclosures OUT of the output entirely."
)

_REQUIRED_SHAPE = """{
  "target_backend": "Higgsfield",
  "prompt": "",
  "negative_prompt": "",
  "metadata": {"duration": 20, "aspect_ratio": "9:16", "language": "en", "version": "1.0"}
}"""


def build_prompt_compiler_prompt(storyboard: Storyboard) -> str:
    """Return the user prompt for prompt compilation."""
    storyboard_json = json.dumps(storyboard.to_dict(), ensure_ascii=False, indent=2)
    return (
        "Compile this storyboard into a vertical-video generation prompt.\n\n"
        "Reasoning goals:\n"
        "- Preserve product identity and scene continuity across the prompt.\n"
        "- Cover camera, lighting, composition, motion, environment, subject action, "
        "pacing, and visual constraints in `prompt`.\n"
        "- Produce a useful `negative_prompt`.\n"
        "- Put non-prompt production info in `metadata` "
        "(duration, aspect_ratio, language, version).\n"
        "- `target_backend` should be \"Higgsfield\".\n\n"
        f"STORYBOARD (JSON):\n{storyboard_json}\n\n"
        f"Return JSON with exactly this shape and keys:\n{_REQUIRED_SHAPE}\n\n"
        f"{JSON_OUTPUT_RULES}"
    )
