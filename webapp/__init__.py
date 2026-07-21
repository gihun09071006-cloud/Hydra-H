"""HYDRA local web app (TASK-028).

A local, offline application for source-based short-form editing. The user
uploads one Coupang product JSON and exactly five local source videos; HYDRA
generates a full editing plan — video metadata, source-role assignments, a clip
timeline, Korean narration and captions, a BGM recommendation, an SFX cue plan,
and publishing copy — plus an optional ffmpeg preview render.

Everything in this package runs locally and offline by default. It performs no
network calls and uses no paid or AI APIs. The only external process it may
invoke is a locally installed ``ffmpeg``/``ffprobe`` (optional; used solely for
the preview render), and it degrades gracefully when they are absent.
"""

from __future__ import annotations

__all__ = ["shortform_editor", "media", "multipart", "server"]
