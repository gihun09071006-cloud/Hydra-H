"""Prompt builders for HYDRA's AI provider.

Pure functions that turn contract objects into prompt strings. They contain no
API calls and no secrets, and they demand strict JSON-only output from the model.
"""

from prompts._rules import JSON_OUTPUT_RULES
from prompts.creative_strategy import (
    SYSTEM_PROMPT as CREATIVE_STRATEGY_SYSTEM,
    build_creative_strategy_prompt,
)
from prompts.product_intelligence import (
    SYSTEM_PROMPT as PRODUCT_INTELLIGENCE_SYSTEM,
    build_product_intelligence_prompt,
)
from prompts.prompt_compiler import (
    SYSTEM_PROMPT as PROMPT_COMPILER_SYSTEM,
    build_prompt_compiler_prompt,
)
from prompts.story import (
    SYSTEM_PROMPT as STORY_SYSTEM,
    build_story_prompt,
)

__all__ = [
    "JSON_OUTPUT_RULES",
    "PRODUCT_INTELLIGENCE_SYSTEM",
    "build_product_intelligence_prompt",
    "CREATIVE_STRATEGY_SYSTEM",
    "build_creative_strategy_prompt",
    "STORY_SYSTEM",
    "build_story_prompt",
    "PROMPT_COMPILER_SYSTEM",
    "build_prompt_compiler_prompt",
]
