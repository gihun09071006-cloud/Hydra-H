"""Local HTTP server for the HYDRA short-form editing web app (TASK-028).

Stdlib-only (``http.server``). Serves a single upload page, accepts one product
JSON plus exactly five source videos, runs the offline editing-plan generator,
optionally renders an ffmpeg preview, and shows the result with download links.

Runs locally and offline. It binds to localhost by default and makes no
outbound network calls.
"""

from __future__ import annotations

import html
import json
import mimetypes
import os
import re
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Optional

from contracts.product_facts import ProductFacts
from runtime.extension_facts import product_facts_from_extension
from webapp import media
from webapp.multipart import MultipartError, parse_boundary, parse_multipart
from webapp.shortform_editor import (
    REQUIRED_VIDEO_COUNT,
    PlanError,
    VideoInput,
    build_plan,
    probe_videos,
)

# Reject absurdly large request bodies (local tool, but stay defensive).
MAX_BODY_BYTES = 4 * 1024 * 1024 * 1024  # 4 GiB
_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_filename(name: str, fallback: str) -> str:
    base = os.path.basename(name or "").strip() or fallback
    base = _SAFE_NAME.sub("_", base)
    return base or fallback


def facts_from_product_json(raw: bytes) -> ProductFacts:
    """Parse an uploaded product JSON into :class:`ProductFacts`.

    Accepts the browser-extension export format first; falls back to a plain
    ProductFacts-shaped object. Raises :class:`PlanError` on invalid input.
    """
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PlanError(f"product JSON is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise PlanError("product JSON must be a JSON object")
    try:
        return product_facts_from_extension(data)
    except ValueError:
        facts = ProductFacts.from_dict(data)
        if not (facts.product_name and str(facts.product_name).strip()):
            raise PlanError("product JSON is missing 'product_name'")
        return facts


class HydraServer(ThreadingHTTPServer):
    """Threading HTTP server carrying app configuration."""

    daemon_threads = True

    def __init__(self, server_address, handler, *, output_dir: str, enable_preview: bool):
        super().__init__(server_address, handler)
        self.output_dir = output_dir
        self.enable_preview = enable_preview
        os.makedirs(output_dir, exist_ok=True)


class HydraRequestHandler(BaseHTTPRequestHandler):
    server_version = "HYDRA-Local/1.0"

    # ------------------------------------------------------------------ #
    # Routing.                                                           #
    # ------------------------------------------------------------------ #
    def do_GET(self) -> None:  # noqa: N802 (http.server API)
        path = self.path.split("?", 1)[0]
        if path == "/":
            self._send_html(200, _render_upload_page())
        elif path == "/health":
            self._send_bytes(200, b"ok", "text/plain; charset=utf-8")
        elif path.startswith("/runs/"):
            self._serve_run_file(path)
        else:
            self._send_html(404, _render_message_page("404", "페이지를 찾을 수 없습니다."))

    def do_POST(self) -> None:  # noqa: N802 (http.server API)
        if self.path.split("?", 1)[0] != "/generate":
            self._send_html(404, _render_message_page("404", "지원하지 않는 경로입니다."))
            return
        try:
            self._handle_generate()
        except (PlanError, MultipartError) as exc:
            self._send_html(400, _render_message_page("입력 오류", str(exc)))
        except Exception as exc:  # noqa: BLE001 (surface any failure to the page)
            self._send_html(500, _render_message_page("서버 오류", str(exc)))

    # ------------------------------------------------------------------ #
    # /generate.                                                         #
    # ------------------------------------------------------------------ #
    def _handle_generate(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            raise PlanError("빈 요청입니다. 파일을 첨부해 주세요.")
        if length > MAX_BODY_BYTES:
            raise PlanError("업로드 용량이 너무 큽니다.")

        boundary = parse_boundary(self.headers.get("Content-Type", ""))
        body = self._read_exact(length)
        form = parse_multipart(body, boundary)

        product_part = form.get("product_json")
        if product_part is None or not product_part.data:
            raise PlanError("쿠팡 상품 JSON 파일을 첨부해 주세요.")
        facts = facts_from_product_json(product_part.data)

        video_parts = [p for p in form.files("videos") if p.data]
        if len(video_parts) != REQUIRED_VIDEO_COUNT:
            raise PlanError(
                f"소스 영상은 정확히 {REQUIRED_VIDEO_COUNT}개를 첨부해야 합니다 "
                f"(현재 {len(video_parts)}개)."
            )

        run_id = f"run_{time.strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"
        run_dir = os.path.join(self.server.output_dir, run_id)
        os.makedirs(run_dir, exist_ok=True)

        videos: list[VideoInput] = []
        source_paths: dict[str, str] = {}
        for index, part in enumerate(video_parts, start=1):
            fname = _safe_filename(part.filename or "", f"source_{index}.mp4")
            # Avoid collisions when two uploads share a name.
            fname = f"{index:02d}_{fname}"
            dest = os.path.join(run_dir, fname)
            with open(dest, "wb") as handle:
                handle.write(part.data)
            videos.append(VideoInput(filename=fname, path=dest))
            source_paths[fname] = dest

        # Probe durations locally (no-op without ffprobe).
        videos = probe_videos(videos, media.probe_duration if media.ffprobe_available() else None)

        plan = build_plan(facts, videos, require_five=True)

        want_preview = (form.value("make_preview") or "") in ("1", "on", "true")
        preview_status: dict[str, Any] = {"ok": False, "output_path": None, "reason": None}
        if want_preview and self.server.enable_preview:
            preview_path = os.path.join(run_dir, "preview.mp4")
            preview_status = media.render_preview(
                plan["clip_timeline"], source_paths, preview_path
            )
        elif want_preview and not self.server.enable_preview:
            preview_status["reason"] = "미리보기가 비활성화되어 있습니다."
        plan["preview"] = {
            "requested": want_preview,
            "available": bool(preview_status.get("ok")),
            "note": preview_status.get("reason"),
        }

        plan_path = os.path.join(run_dir, "plan.json")
        with open(plan_path, "w", encoding="utf-8") as handle:
            json.dump(plan, handle, ensure_ascii=False, indent=2)

        preview_url = (
            f"/runs/{run_id}/preview.mp4" if preview_status.get("ok") else None
        )
        self._send_html(
            200,
            _render_result_page(
                run_id=run_id,
                plan=plan,
                plan_url=f"/runs/{run_id}/plan.json",
                preview_url=preview_url,
                preview_note=preview_status.get("reason"),
            ),
        )

    # ------------------------------------------------------------------ #
    # Static run files (plan.json, preview.mp4).                         #
    # ------------------------------------------------------------------ #
    def _serve_run_file(self, path: str) -> None:
        parts = path.strip("/").split("/")
        # Expected: runs/<run_id>/<filename>
        if len(parts) != 3:
            self._send_html(404, _render_message_page("404", "잘못된 경로입니다."))
            return
        _, run_id, filename = parts
        run_id = _SAFE_NAME.sub("_", run_id)
        filename = _safe_filename(filename, "")
        if not filename:
            self._send_html(404, _render_message_page("404", "파일을 찾을 수 없습니다."))
            return
        full = os.path.realpath(os.path.join(self.server.output_dir, run_id, filename))
        root = os.path.realpath(self.server.output_dir)
        if not full.startswith(root + os.sep) or not os.path.isfile(full):
            self._send_html(404, _render_message_page("404", "파일을 찾을 수 없습니다."))
            return
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        with open(full, "rb") as handle:
            data = handle.read()
        self._send_bytes(200, data, ctype)

    # ------------------------------------------------------------------ #
    # Low-level helpers.                                                 #
    # ------------------------------------------------------------------ #
    def _read_exact(self, length: int) -> bytes:
        chunks = []
        remaining = length
        while remaining > 0:
            chunk = self.rfile.read(min(remaining, 1024 * 1024))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def _send_html(self, status: int, body: str) -> None:
        self._send_bytes(status, body.encode("utf-8"), "text/html; charset=utf-8")

    def _send_bytes(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def log_message(self, fmt: str, *args: Any) -> None:  # keep console quiet-ish
        return


# ---------------------------------------------------------------------- #
# HTML rendering (self-contained, no external assets — fully offline).   #
# ---------------------------------------------------------------------- #

_STYLE = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body { font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans KR", sans-serif;
       margin: 0; background: #0f1115; color: #e8eaed; }
.wrap { max-width: 860px; margin: 0 auto; padding: 32px 20px 64px; }
h1 { font-size: 1.6rem; margin: 0 0 4px; }
h2 { font-size: 1.1rem; margin: 28px 0 10px; border-bottom: 1px solid #2a2e37; padding-bottom: 6px; }
.sub { color: #9aa0aa; margin: 0 0 24px; }
.card { background: #171a21; border: 1px solid #262b35; border-radius: 12px; padding: 20px; margin: 16px 0; }
label { display: block; font-weight: 600; margin: 14px 0 6px; }
input[type=file] { width: 100%; padding: 10px; background: #0f1115; border: 1px dashed #333a47;
                   border-radius: 8px; color: #cfd3da; }
.hint { color: #8b909b; font-size: 0.85rem; margin-top: 4px; }
.check { display: flex; align-items: center; gap: 8px; margin-top: 16px; font-weight: 600; }
button { margin-top: 20px; background: #3b82f6; color: #fff; border: 0; border-radius: 8px;
         padding: 12px 22px; font-size: 1rem; font-weight: 600; cursor: pointer; }
button:hover { background: #2f6fe0; }
pre { background: #0b0d11; border: 1px solid #222; border-radius: 8px; padding: 14px;
      overflow-x: auto; font-size: 0.82rem; line-height: 1.5; }
a { color: #6ea8fe; }
.pill { display: inline-block; background: #1f2a3d; color: #9ec5ff; border-radius: 999px;
        padding: 3px 12px; font-size: 0.8rem; margin-right: 6px; }
.grid { display: grid; gap: 6px; }
.warn { color: #ffcf6e; }
.err { color: #ff8a8a; }
table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid #232833; vertical-align: top; }
th { color: #9aa0aa; font-weight: 600; }
.footer { margin-top: 40px; color: #6b7180; font-size: 0.8rem; }
"""


def _page(title: str, body: str) -> str:
    return (
        "<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{html.escape(title)}</title><style>{_STYLE}</style></head>"
        f"<body><div class='wrap'>{body}"
        "<div class='footer'>HYDRA · 로컬/오프라인 · 외부 API·네트워크 호출 없음</div>"
        "</div></body></html>"
    )


def _render_upload_page() -> str:
    body = f"""
    <h1>HYDRA · 소스 기반 쇼츠 편집</h1>
    <p class='sub'>쿠팡 상품 JSON 1개와 로컬 소스 영상 정확히 {REQUIRED_VIDEO_COUNT}개를 올리면,
       편집 계획(메타데이터·역할 배정·타임라인·한국어 나레이션/자막·BGM·효과음·발행 문구)을 생성합니다.</p>
    <form class='card' method='post' action='/generate' enctype='multipart/form-data'>
      <label>1) 쿠팡 상품 JSON</label>
      <input type='file' name='product_json' accept='.json,application/json' required>
      <div class='hint'>브라우저 확장 프로그램이 내보낸 상품 JSON을 사용하세요.</div>

      <label>2) 소스 영상 {REQUIRED_VIDEO_COUNT}개</label>
      <input type='file' name='videos' accept='video/*' multiple required>
      <div class='hint'>정확히 {REQUIRED_VIDEO_COUNT}개를 선택하세요. 업로드 순서대로 훅→문제→해결→증거→행동유도에 배정됩니다.</div>

      <label class='check'><input type='checkbox' name='make_preview' value='1'>
        ffmpeg 미리보기 영상 만들기 (설치되어 있을 때만)</label>

      <button type='submit'>편집 계획 생성</button>
    </form>
    """
    return _page("HYDRA 로컬 쇼츠 편집", body)


def _render_message_page(heading: str, message: str) -> str:
    body = (
        f"<h1>{html.escape(heading)}</h1>"
        f"<div class='card err'>{html.escape(message)}</div>"
        "<p><a href='/'>← 처음으로</a></p>"
    )
    return _page(f"HYDRA · {heading}", body)


def _kv_table(rows: list[tuple[str, Any]]) -> str:
    cells = "".join(
        f"<tr><th>{html.escape(str(k))}</th><td>{html.escape('' if v is None else str(v))}</td></tr>"
        for k, v in rows
    )
    return f"<table>{cells}</table>"


def _scene_table(items: list[dict], columns: list[tuple[str, str]]) -> str:
    head = "".join(f"<th>{html.escape(label)}</th>" for _, label in columns)
    body_rows = []
    for item in items:
        cells = "".join(
            f"<td>{html.escape('' if item.get(key) is None else str(item.get(key)))}</td>"
            for key, _ in columns
        )
        body_rows.append(f"<tr>{cells}</tr>")
    return f"<table><tr>{head}</tr>{''.join(body_rows)}</table>"


def _render_result_page(
    *,
    run_id: str,
    plan: dict[str, Any],
    plan_url: str,
    preview_url: Optional[str],
    preview_note: Optional[str],
) -> str:
    meta = plan.get("video_metadata", {})
    market = plan.get("market_fit", {})
    pub = plan.get("publishing_copy", {})
    bgm = plan.get("bgm_recommendation", {})

    parts: list[str] = []
    parts.append("<h1>편집 계획 생성 완료</h1>")
    parts.append(
        f"<p class='sub'>실행 ID <code>{html.escape(run_id)}</code> · "
        f"판정 <span class='pill'>{html.escape(str(market.get('decision')))}</span> "
        f"점수 <span class='pill'>{html.escape(str(market.get('score')))}/100</span></p>"
    )

    # Downloads / preview.
    dl = [f"<a href='{html.escape(plan_url)}' download>plan.json 다운로드</a>"]
    parts.append("<div class='card'>" + " · ".join(dl) + "</div>")
    if preview_url:
        parts.append(
            "<h2>미리보기</h2>"
            f"<video src='{html.escape(preview_url)}' controls "
            "style='max-width:320px;width:100%;border-radius:10px;background:#000'></video>"
        )
    elif preview_note:
        parts.append(f"<p class='warn'>미리보기: {html.escape(preview_note)}</p>")

    # Metadata.
    parts.append("<h2>영상 메타데이터</h2>")
    parts.append(
        "<div class='card'>"
        + _kv_table(
            [
                ("제목", meta.get("title")),
                ("비율/해상도", f"{meta.get('aspect_ratio')} · {meta.get('resolution')} @ {meta.get('fps')}fps"),
                ("길이(초)", meta.get("total_duration_sec")),
                ("전략", meta.get("strategy")),
                ("스토리 패턴", meta.get("story_pattern")),
                ("상품 링크", meta.get("product_url")),
            ]
        )
        + "</div>"
    )

    # Timeline + roles.
    parts.append("<h2>타임라인 · 소스 역할</h2>")
    parts.append(
        "<div class='card'>"
        + _scene_table(
            plan.get("clip_timeline", []),
            [
                ("scene", "#"),
                ("role", "역할"),
                ("timeline_start_sec", "시작"),
                ("timeline_end_sec", "끝"),
                ("source_video", "소스"),
                ("transition_out", "전환"),
            ],
        )
        + "</div>"
    )

    # Narration + captions.
    parts.append("<h2>한국어 나레이션 · 자막</h2>")
    narr_rows = []
    captions = {c["scene"]: c for c in plan.get("captions", [])}
    for item in plan.get("narration", []):
        cap = captions.get(item["scene"], {})
        narr_rows.append(
            {
                "scene": item["scene"],
                "role": item["role"],
                "narration": item["text"],
                "caption": cap.get("text"),
            }
        )
    parts.append(
        "<div class='card'>"
        + _scene_table(
            narr_rows,
            [("scene", "#"), ("role", "역할"), ("narration", "나레이션"), ("caption", "자막")],
        )
        + "</div>"
    )

    # BGM + SFX.
    parts.append("<h2>BGM · 효과음</h2>")
    parts.append(
        "<div class='card'>"
        + _kv_table(
            [
                ("BGM 무드", bgm.get("mood")),
                ("장르", bgm.get("genre")),
                ("BPM", bgm.get("bpm_range")),
                ("드롭 시점(초)", bgm.get("drop_at_sec")),
                ("라이선스", bgm.get("license_note")),
            ]
        )
        + _scene_table(
            plan.get("sfx_cue_plan", []),
            [("at_sec", "시각(초)"), ("role", "역할"), ("sfx", "효과음"), ("purpose", "용도")],
        )
        + "</div>"
    )

    # Publishing copy.
    parts.append("<h2>발행 문구</h2>")
    parts.append(
        "<div class='card'>"
        + _kv_table(
            [
                ("제목", pub.get("title")),
                ("설명", pub.get("description")),
                ("해시태그", " ".join(pub.get("hashtags", []))),
                ("CTA", pub.get("call_to_action")),
            ]
        )
        + f"<p class='hint'>{html.escape(str(pub.get('affiliate_disclosure')))}</p>"
        + "</div>"
    )

    # Full JSON.
    parts.append("<h2>전체 계획 (JSON)</h2>")
    pretty = json.dumps(plan, ensure_ascii=False, indent=2)
    parts.append(f"<pre>{html.escape(pretty)}</pre>")

    parts.append("<p><a href='/'>← 새 계획 만들기</a></p>")
    return _page("HYDRA · 편집 계획", "".join(parts))


def run_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    *,
    output_dir: str,
    enable_preview: bool = True,
) -> HydraServer:
    """Create (but do not serve) a configured :class:`HydraServer`."""
    server = HydraServer(
        (host, port),
        HydraRequestHandler,
        output_dir=output_dir,
        enable_preview=enable_preview,
    )
    return server
