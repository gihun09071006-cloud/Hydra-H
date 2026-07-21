"""Unit tests for the shared JSON response parser."""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from providers.json_response_parser import (  # noqa: E402
    ProviderResponseError,
    parse_json_response,
)


class Block:
    def __init__(self, text, type="text"):
        self.type = type
        self.text = text


class Response:
    def __init__(self, content):
        self.content = content


def test_parses_valid_json_object():
    resp = Response([Block('{"a": 1, "b": [1, 2]}')])
    assert parse_json_response(resp) == {"a": 1, "b": [1, 2]}


def test_concatenates_multiple_text_blocks():
    resp = Response([Block('{"a":'), Block(" 1}")])
    assert parse_json_response(resp) == {"a": 1}


def test_no_content_rejected():
    with pytest.raises(ProviderResponseError):
        parse_json_response(Response([]))


def test_no_text_blocks_rejected():
    with pytest.raises(ProviderResponseError):
        parse_json_response(Response([Block("ignored", type="thinking")]))


def test_markdown_fence_rejected():
    resp = Response([Block('```json\n{"a": 1}\n```')])
    with pytest.raises(ProviderResponseError):
        parse_json_response(resp)


def test_prose_around_json_rejected():
    with pytest.raises(ProviderResponseError):
        parse_json_response(Response([Block('Here you go: {"a": 1}')]))
    with pytest.raises(ProviderResponseError):
        parse_json_response(Response([Block('{"a": 1} hope that helps')]))


def test_non_object_rejected():
    with pytest.raises(ProviderResponseError):
        parse_json_response(Response([Block("[1, 2, 3]")]))


def test_invalid_json_rejected():
    with pytest.raises(ProviderResponseError):
        parse_json_response(Response([Block("{not valid json}")]))


def test_whitespace_trimmed():
    resp = Response([Block('  \n {"a": 1} \n ')])
    assert parse_json_response(resp) == {"a": 1}
