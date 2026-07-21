"""Local ffmpeg / ffprobe helpers for the optional preview render (TASK-028).

The preview is strictly optional. Everything here degrades gracefully when
``ffmpeg``/``ffprobe`` are not installed — the app still produces the full
editing plan without them.

These helpers only ever invoke a **locally installed** ffmpeg/ffprobe via
``subprocess``. They perform no network access and download nothing.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Optional

from webapp.shortform_editor import TARGET_FPS, TARGET_HEIGHT, TARGET_WIDTH

# Guard the preview against pathological renders on a local machine.
_RENDER_TIMEOUT_SEC = 600
_PROBE_TIMEOUT_SEC = 30


def ffmpeg_available() -> bool:
    """True when a local ``ffmpeg`` binary is on PATH."""
    return shutil.which("ffmpeg") is not None


def ffprobe_available() -> bool:
    """True when a local ``ffprobe`` binary is on PATH."""
    return shutil.which("ffprobe") is not None


def probe_duration(path: str) -> Optional[float]:
    """Return the duration of ``path`` in seconds, or ``None`` if unavailable.

    Never raises: any failure (missing ffprobe, unreadable file, malformed
    output) yields ``None`` so callers can proceed without durations.
    """
    ffprobe = shutil.which("ffprobe")
    if not ffprobe or not path:
        return None
    try:
        result = subprocess.run(
            [
                ffprobe,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                path,
            ],
            capture_output=True,
            text=True,
            timeout=_PROBE_TIMEOUT_SEC,
            check=False,
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout or "{}")
        duration = data.get("format", {}).get("duration")
        value = float(duration)
        return value if value > 0 else None
    except (subprocess.SubprocessError, ValueError, OSError, json.JSONDecodeError):
        return None


def build_preview_command(
    timeline: list[dict],
    source_paths: dict[str, str],
    output_path: str,
) -> Optional[list[str]]:
    """Build the ffmpeg argv that renders a 9:16 preview from the timeline.

    Each timeline scene contributes a segment trimmed to its ``source_in_sec``/
    ``source_out_sec`` window, scaled and padded to the vertical target, then all
    segments are concatenated (video only — a silent preview). Returns ``None``
    when there is nothing renderable (no ffmpeg, or no scene has a real source
    file on disk).

    This is a pure function (no subprocess); :func:`render_preview` runs it.
    """
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None

    inputs: list[str] = []
    filters: list[str] = []
    concat_labels: list[str] = []
    input_index = 0

    for scene in timeline:
        source = scene.get("source_video")
        path = source_paths.get(source)
        if not path:
            continue
        start = float(scene.get("source_in_sec", 0.0) or 0.0)
        end = float(scene.get("source_out_sec", 0.0) or 0.0)
        seg = max(end - start, 0.1)  # guard against zero/negative-length trims

        inputs += ["-i", path]
        label = f"v{input_index}"
        # Trim, reset PTS, scale to fit inside the frame, pad to exact 9:16.
        filters.append(
            f"[{input_index}:v]trim=start={start:.3f}:duration={seg:.3f},"
            f"setpts=PTS-STARTPTS,"
            f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"setsar=1,fps={TARGET_FPS},format=yuv420p[{label}]"
        )
        concat_labels.append(f"[{label}]")
        input_index += 1

    if input_index == 0:
        return None

    concat = "".join(concat_labels) + f"concat=n={input_index}:v=1:a=0[outv]"
    filter_complex = ";".join(filters + [concat])

    return [
        ffmpeg,
        "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-r", str(TARGET_FPS),
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path,
    ]


def render_preview(
    timeline: list[dict],
    source_paths: dict[str, str],
    output_path: str,
) -> dict:
    """Render the optional preview. Returns a status dict; never raises.

    Result shape::

        {"ok": bool, "output_path": str | None, "reason": str | None}
    """
    if not ffmpeg_available():
        return {
            "ok": False,
            "output_path": None,
            "reason": "ffmpeg를 찾을 수 없습니다. 미리보기 없이 편집 계획만 생성했습니다.",
        }

    command = build_preview_command(timeline, source_paths, output_path)
    if command is None:
        return {
            "ok": False,
            "output_path": None,
            "reason": "미리보기를 만들 소스 영상이 없습니다.",
        }

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=_RENDER_TIMEOUT_SEC,
            check=False,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        return {"ok": False, "output_path": None, "reason": f"미리보기 렌더 실패: {exc}"}

    if result.returncode != 0:
        tail = (result.stderr or "").strip().splitlines()
        detail = tail[-1] if tail else "알 수 없는 오류"
        return {"ok": False, "output_path": None, "reason": f"ffmpeg 오류: {detail}"}

    return {"ok": True, "output_path": output_path, "reason": None}
