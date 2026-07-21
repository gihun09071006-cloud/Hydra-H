"""Minimal ``multipart/form-data`` parser (stdlib only).

Python's ``cgi.FieldStorage`` was removed in 3.13, so this module implements the
small slice of multipart parsing the upload form needs — no third-party
dependencies, no network. It parses an in-memory request body into named parts.

Each part exposes its form ``name``, optional ``filename``, ``content_type``,
and raw ``data`` bytes. Binary uploads (videos) are preserved byte-for-byte.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Part:
    name: str
    filename: Optional[str] = None
    content_type: Optional[str] = None
    data: bytes = b""

    @property
    def is_file(self) -> bool:
        return self.filename is not None

    def text(self, encoding: str = "utf-8") -> str:
        return self.data.decode(encoding)


@dataclass
class MultipartForm:
    parts: list[Part] = field(default_factory=list)

    def get(self, name: str) -> Optional[Part]:
        for part in self.parts:
            if part.name == name:
                return part
        return None

    def files(self, name: str) -> list[Part]:
        return [p for p in self.parts if p.name == name and p.is_file]

    def value(self, name: str) -> Optional[str]:
        part = self.get(name)
        return part.text() if part is not None else None


class MultipartError(ValueError):
    """Raised when the request body is not valid multipart/form-data."""


def parse_boundary(content_type: str) -> bytes:
    """Extract the boundary token from a ``Content-Type`` header value."""
    if not content_type:
        raise MultipartError("missing Content-Type header")
    ctype = content_type.split(";")
    if not ctype[0].strip().lower().startswith("multipart/form-data"):
        raise MultipartError("Content-Type is not multipart/form-data")
    for param in ctype[1:]:
        key, _, val = param.strip().partition("=")
        if key.strip().lower() == "boundary":
            token = val.strip().strip('"')
            if not token:
                raise MultipartError("empty multipart boundary")
            return token.encode("latin-1")
    raise MultipartError("multipart boundary not found")


def _parse_headers(raw: bytes) -> dict[str, str]:
    headers: dict[str, str] = {}
    for line in raw.split(b"\r\n"):
        if not line:
            continue
        key, sep, val = line.partition(b":")
        if not sep:
            continue
        headers[key.decode("latin-1").strip().lower()] = val.decode("latin-1").strip()
    return headers


def _parse_content_disposition(value: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for item in value.split(";"):
        key, sep, val = item.strip().partition("=")
        if sep:
            fields[key.strip().lower()] = val.strip().strip('"')
        else:
            fields[key.strip().lower()] = ""
    return fields


def parse_multipart(body: bytes, boundary: bytes) -> MultipartForm:
    """Parse an in-memory multipart/form-data body into a :class:`MultipartForm`."""
    if not body:
        raise MultipartError("empty request body")

    delimiter = b"--" + boundary
    # Split on the delimiter; the first chunk is a preamble and the last is the
    # closing terminator ("--\r\n"), both discarded.
    segments = body.split(delimiter)
    parts: list[Part] = []

    for segment in segments[1:]:
        if segment in (b"", b"--", b"--\r\n", b"\r\n"):
            continue
        if segment.startswith(b"--"):  # closing boundary "--\r\n"
            break
        # Each segment starts with CRLF then headers, then CRLFCRLF, then data,
        # then a trailing CRLF before the next delimiter.
        segment = segment[2:] if segment.startswith(b"\r\n") else segment
        header_block, sep, data = segment.partition(b"\r\n\r\n")
        if not sep:
            continue
        if data.endswith(b"\r\n"):
            data = data[:-2]

        headers = _parse_headers(header_block)
        disposition = headers.get("content-disposition", "")
        if not disposition:
            continue
        disp_fields = _parse_content_disposition(disposition)
        name = disp_fields.get("name")
        if name is None:
            continue
        filename = disp_fields.get("filename")
        parts.append(
            Part(
                name=name,
                filename=filename if filename not in (None, "") else None,
                content_type=headers.get("content-type"),
                data=data,
            )
        )

    return MultipartForm(parts=parts)
