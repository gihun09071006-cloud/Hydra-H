"""Shared strict-JSON parser for Claude provider responses.

Collects text from an Anthropic response, enforces JSON-only output, and returns
a dict. Rejects empty content, Markdown code fences, prose around the JSON, and
non-object JSON. No aggressive repair, no ``eval``.
"""

from __future__ import annotations

import json
from typing import Any


class ProviderResponseError(Exception):
    """Raised when a provider response is missing or not strict JSON."""


def _collect_text(response: Any) -> str:
    """Concatenate the text blocks of an Anthropic response."""
    content = getattr(response, "content", None)
    if not content:
        raise ProviderResponseError("provider response has no content")

    parts: list[str] = []
    for block in content:
        block_type = getattr(block, "type", None)
        if block_type is None and isinstance(block, dict):
            block_type = block.get("type")
        if block_type != "text":
            continue
        text = getattr(block, "text", None)
        if text is None and isinstance(block, dict):
            text = block.get("text")
        if text:
            parts.append(text)

    if not parts:
        raise ProviderResponseError("provider response has no text content")
    return "".join(parts)


def parse_json_response(response: Any) -> dict[str, Any]:
    """Return a dict parsed from the response's text, or raise ProviderResponseError."""
    text = _collect_text(response).strip()
    if not text:
        raise ProviderResponseError("provider response text is empty")
    if text.startswith("```") or "```" in text:
        raise ProviderResponseError("provider response contains a Markdown code fence")
    if not (text.startswith("{") and text.endswith("}")):
        raise ProviderResponseError("provider response is not a bare JSON object")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProviderResponseError(f"provider response is not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ProviderResponseError("provider response JSON is not a top-level object")
    return data
