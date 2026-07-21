"""RenderPrompt contract — output of the Prompt Compiler.

Data only.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class RenderMetadata:
    duration: int = 0
    aspect_ratio: str = ""
    language: str = ""
    version: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RenderMetadata":
        data = data or {}
        return cls(
            duration=data.get("duration", 0),
            aspect_ratio=data.get("aspect_ratio", ""),
            language=data.get("language", ""),
            version=data.get("version", ""),
        )


@dataclass
class RenderPrompt:
    target_backend: str = ""
    prompt: str = ""
    negative_prompt: str = ""
    metadata: RenderMetadata = field(default_factory=RenderMetadata)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RenderPrompt":
        data = data or {}
        return cls(
            target_backend=data.get("target_backend", ""),
            prompt=data.get("prompt", ""),
            negative_prompt=data.get("negative_prompt", ""),
            metadata=RenderMetadata.from_dict(data.get("metadata", {})),
        )
