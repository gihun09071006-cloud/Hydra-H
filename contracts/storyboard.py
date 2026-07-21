"""Storyboard contract — output of the Story Engine.

Data only.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Scene:
    scene: int = 0
    duration: int = 0
    goal: str = ""
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Scene":
        data = data or {}
        return cls(
            scene=data.get("scene", 0),
            duration=data.get("duration", 0),
            goal=data.get("goal", ""),
            description=data.get("description", ""),
        )


@dataclass
class Storyboard:
    story_pattern: str = ""
    duration: int = 20
    scenes: list[Scene] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Storyboard":
        data = data or {}
        return cls(
            story_pattern=data.get("story_pattern", ""),
            duration=data.get("duration", 20),
            scenes=[Scene.from_dict(s) for s in data.get("scenes") or []],
        )
