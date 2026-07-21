"""CreativeStrategy contract — output of the Creative Strategy Engine.

Data only.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class CreativeStrategy:
    strategy: str = ""
    reason: str = ""
    confidence: int = 0
    hook_type: str = ""
    story_pattern: str = ""
    cta_style: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CreativeStrategy":
        data = data or {}
        return cls(
            strategy=data.get("strategy", ""),
            reason=data.get("reason", ""),
            confidence=data.get("confidence", 0),
            hook_type=data.get("hook_type", ""),
            story_pattern=data.get("story_pattern", ""),
            cta_style=data.get("cta_style", ""),
        )
