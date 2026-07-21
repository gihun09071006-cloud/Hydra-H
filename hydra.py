#!/usr/bin/env python3
"""HYDRA command-line runner.

Usage::

    # URL mode (fetch over HTTP)
    python hydra.py "https://link.coupang.com/a/example"
    python hydra.py "https://www.coupang.com/vp/products/123456789"

    # Local HTML mode (when direct fetching is blocked, e.g. HTTP 403)
    python hydra.py --html-file "D:\\path\\product.html" \\
        --source-url "https://link.coupang.com/a/example"

Runs the existing :class:`HydraPipeline` and prints the returned RenderPrompt as
indented UTF-8 JSON. Exit code 0 on success, non-zero on failure.

This module is composition and user I/O only. It contains no scraping, parsing,
AI, marketing, scoring, prompt, or state-machine logic, and it does not
duplicate any pipeline step — all of that lives in the reused components.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

from providers.factory import ProviderFactory
from runtime.hydra_pipeline import HydraPipeline


def _build_pipeline() -> HydraPipeline:
    """Compose the existing components: Claude placeholder provider + pipeline."""
    provider = ProviderFactory.create("claude")
    return HydraPipeline(provider=provider)


def main(argv: Optional[Sequence[str]] = None, pipeline: Optional[HydraPipeline] = None) -> int:
    """CLI entry point. Returns an exit code (0 success, non-zero failure)."""
    parser = argparse.ArgumentParser(
        prog="hydra.py",
        description="Run the HYDRA pipeline for a Coupang URL and print a RenderPrompt.",
    )
    parser.add_argument(
        "url", nargs="?", help="Coupang affiliate link or direct product URL (URL mode)"
    )
    parser.add_argument(
        "--html-file", dest="html_file",
        help="Path to a locally saved Coupang product-page HTML file (local HTML mode)",
    )
    parser.add_argument(
        "--source-url", dest="source_url",
        help="Original Coupang URL for the saved HTML, preserved as source metadata",
    )

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse already wrote a concise usage/error message to stderr.
        return int(exc.code) if exc.code is not None else 2

    # Mode selection: exactly one of URL mode or local HTML mode.
    if args.html_file and args.url:
        print("hydra: error: provide either a URL or --html-file, not both", file=sys.stderr)
        return 2
    if not args.html_file and not args.url:
        print("hydra: error: a URL or --html-file is required", file=sys.stderr)
        return 2
    if args.html_file and not args.source_url:
        print("hydra: error: --source-url is required with --html-file", file=sys.stderr)
        return 2

    try:
        runner = pipeline or _build_pipeline()
        if args.html_file:
            html = Path(args.html_file).read_text(encoding="utf-8")
            render_prompt = runner.run_from_html(html, args.source_url)
        else:
            render_prompt = runner.run(args.url)
        output = json.dumps(render_prompt.to_dict(), indent=2, ensure_ascii=False)
    except FileNotFoundError:
        print(f"hydra: error: file not found: {args.html_file}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - surface a concise message, not a traceback
        print(f"hydra: error: {exc}", file=sys.stderr)
        return 1

    print(output)

    # --- Publishing composition boundary (future work) -----------------------
    # A future step may compose a social post from this RenderPrompt and the
    # affiliate URL. That publishing step — NOT this CLI — must pass a Coupang
    # Partners compliance gate before publication, enforcing the mandatory
    # disclosure text:
    #   "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."
    # This disclosure is intentionally NOT appended to RenderPrompt: RenderPrompt
    # is a video-generation contract, not a publishing contract.
    # -------------------------------------------------------------------------

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
