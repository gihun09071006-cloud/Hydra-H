"""Offline tests for ffmpeg/ffprobe helpers (TASK-028).

No real ffmpeg is invoked: availability is monkeypatched, and the command
builder is a pure function.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from webapp import media  # noqa: E402

TIMELINE = [
    {"source_video": "01.mp4", "source_in_sec": 0.0, "source_out_sec": 3.0},
    {"source_video": "02.mp4", "source_in_sec": 0.0, "source_out_sec": 4.0},
]
PATHS = {"01.mp4": "/tmp/01.mp4", "02.mp4": "/tmp/02.mp4"}


def test_build_preview_command_none_without_ffmpeg(monkeypatch):
    monkeypatch.setattr(media.shutil, "which", lambda name: None)
    assert media.build_preview_command(TIMELINE, PATHS, "/tmp/out.mp4") is None


def test_build_preview_command_when_ffmpeg_present(monkeypatch):
    monkeypatch.setattr(media.shutil, "which", lambda name: "/usr/bin/ffmpeg")
    cmd = media.build_preview_command(TIMELINE, PATHS, "/tmp/out.mp4")
    assert cmd is not None
    assert cmd[0] == "/usr/bin/ffmpeg"
    assert cmd[-1] == "/tmp/out.mp4"
    # Two inputs (one per timeline scene with a real path).
    assert cmd.count("-i") == 2
    assert "-filter_complex" in cmd
    fc = cmd[cmd.index("-filter_complex") + 1]
    assert "concat=n=2:v=1:a=0" in fc


def test_build_preview_command_skips_missing_paths(monkeypatch):
    monkeypatch.setattr(media.shutil, "which", lambda name: "/usr/bin/ffmpeg")
    cmd = media.build_preview_command(TIMELINE, {"01.mp4": "/tmp/01.mp4"}, "/tmp/o.mp4")
    assert cmd.count("-i") == 1  # second scene had no path


def test_render_preview_graceful_without_ffmpeg(monkeypatch):
    monkeypatch.setattr(media, "ffmpeg_available", lambda: False)
    result = media.render_preview(TIMELINE, PATHS, "/tmp/out.mp4")
    assert result["ok"] is False
    assert result["output_path"] is None
    assert "ffmpeg" in result["reason"]


def test_probe_duration_none_without_ffprobe(monkeypatch):
    monkeypatch.setattr(media.shutil, "which", lambda name: None)
    assert media.probe_duration("/tmp/whatever.mp4") is None
