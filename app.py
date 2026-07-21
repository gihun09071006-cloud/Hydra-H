#!/usr/bin/env python3
"""HYDRA Local Web App — source-based short-form editing (TASK-028).

Run it with::

    python app.py

Then open the printed URL in your browser, upload one Coupang product JSON and
exactly five local source videos, and HYDRA generates a full editing plan:
video metadata, source-role assignments, a clip timeline, Korean narration and
captions, a BGM recommendation, an SFX cue plan, and publishing copy — plus an
optional ffmpeg preview render.

This app runs locally and **offline by default**. It binds to localhost, makes
no outbound network calls, and uses no AI or paid APIs. The only external
process it may invoke is a locally installed ``ffmpeg``/``ffprobe`` for the
optional preview; without them the app still produces the full plan.
"""

from __future__ import annotations

import argparse
import os
import sys
import threading
import webbrowser

# Ensure the repo root is importable when run as ``python app.py`` from anywhere.
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from webapp import media  # noqa: E402
from webapp.server import run_server  # noqa: E402


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="app.py",
        description="HYDRA local, offline short-form editing web app.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="bind port (default: 8000)")
    parser.add_argument(
        "--output-dir",
        default=os.path.join(REPO_ROOT, "output", "webapp"),
        help="where generated runs are written (default: output/webapp)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="do not auto-open a browser window",
    )
    parser.add_argument(
        "--no-preview",
        action="store_true",
        help="disable the optional ffmpeg preview render entirely",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    enable_preview = not args.no_preview
    server = run_server(
        host=args.host,
        port=args.port,
        output_dir=args.output_dir,
        enable_preview=enable_preview,
    )
    host, port = server.server_address[0], server.server_address[1]
    url = f"http://{host}:{port}/"

    ffmpeg_note = "사용 가능" if media.ffmpeg_available() else "미설치 (미리보기 비활성 — 계획은 정상 생성)"
    print("=" * 60)
    print("  HYDRA 로컬 쇼츠 편집 웹앱 (오프라인)")
    print("=" * 60)
    print(f"  주소      : {url}")
    print(f"  출력 폴더 : {args.output_dir}")
    print(f"  ffmpeg    : {ffmpeg_note}")
    print("  종료      : Ctrl+C")
    print("=" * 60)

    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n종료합니다.")
    finally:
        server.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
