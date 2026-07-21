"""Offline tests for the minimal multipart/form-data parser (TASK-028)."""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from webapp.multipart import (  # noqa: E402
    MultipartError,
    parse_boundary,
    parse_multipart,
)

BOUNDARY = "----hydraBoundary123"


def _build_body(parts):
    """Build a multipart body from (headers, data-bytes) tuples."""
    out = b""
    delim = ("--" + BOUNDARY).encode()
    for headers, data in parts:
        out += delim + b"\r\n"
        out += headers.encode() + b"\r\n\r\n"
        out += data + b"\r\n"
    out += delim + b"--\r\n"
    return out


def test_parse_boundary():
    ct = f"multipart/form-data; boundary={BOUNDARY}"
    assert parse_boundary(ct) == BOUNDARY.encode()


def test_parse_boundary_quoted():
    ct = f'multipart/form-data; boundary="{BOUNDARY}"'
    assert parse_boundary(ct) == BOUNDARY.encode()


def test_parse_boundary_rejects_non_multipart():
    with pytest.raises(MultipartError):
        parse_boundary("application/json")


def test_text_field():
    body = _build_body([
        ('Content-Disposition: form-data; name="make_preview"', b"1"),
    ])
    form = parse_multipart(body, BOUNDARY.encode())
    assert form.value("make_preview") == "1"


def test_file_fields_preserve_binary():
    blob = bytes(range(256))  # includes CRLF-like bytes and nulls
    body = _build_body([
        ('Content-Disposition: form-data; name="product_json"; filename="p.json"\r\n'
         'Content-Type: application/json', b'{"product_name": "X"}'),
        ('Content-Disposition: form-data; name="videos"; filename="a.mp4"\r\n'
         'Content-Type: video/mp4', blob),
    ])
    form = parse_multipart(body, BOUNDARY.encode())
    product = form.get("product_json")
    assert product.is_file
    assert product.filename == "p.json"
    assert product.data == b'{"product_name": "X"}'
    files = form.files("videos")
    assert len(files) == 1
    assert files[0].data == blob  # byte-for-byte


def test_multiple_files_same_field():
    body = _build_body([
        ('Content-Disposition: form-data; name="videos"; filename="a.mp4"', b"AAA"),
        ('Content-Disposition: form-data; name="videos"; filename="b.mp4"', b"BBB"),
        ('Content-Disposition: form-data; name="videos"; filename="c.mp4"', b"CCC"),
    ])
    form = parse_multipart(body, BOUNDARY.encode())
    files = form.files("videos")
    assert [f.data for f in files] == [b"AAA", b"BBB", b"CCC"]


def test_empty_body_rejected():
    with pytest.raises(MultipartError):
        parse_multipart(b"", BOUNDARY.encode())
