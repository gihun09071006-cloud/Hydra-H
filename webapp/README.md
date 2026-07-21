# HYDRA Local Web App — Source-Based Short-Form Editing

A local, **offline** web app that turns one Coupang product JSON and exactly
five local source videos into a complete short-form (9:16) editing plan.

## Run

```bash
python app.py
```

Then open the printed URL (default `http://127.0.0.1:8000/`) in your browser.

Options:

| Flag | Default | Meaning |
| --- | --- | --- |
| `--host` | `127.0.0.1` | Bind host |
| `--port` | `8000` | Bind port |
| `--output-dir` | `output/webapp` | Where generated runs are written |
| `--no-browser` | off | Do not auto-open a browser |
| `--no-preview` | off | Disable the optional ffmpeg preview entirely |

## What you upload

1. **One Coupang product JSON** — the export from the HYDRA browser extension
   (or any object with at least `product_name`).
2. **Exactly five source videos** — uploaded in the order they should play.

## What it generates

For every run the app writes `output/webapp/run_<timestamp>/plan.json` and shows
it in the browser:

- **video_metadata** — title, orientation, aspect ratio (9:16), resolution
  (1080×1920), fps, total duration, strategy, story pattern.
- **source_role_assignments** — each uploaded clip mapped to a narrative role:
  Hook → Problem → Solution → Proof → CTA (upload order; reorderable).
- **clip_timeline** — a contiguous per-scene timeline with playhead times,
  source in/out points, and transitions. Clips shorter than their scene are
  flagged.
- **narration** — Korean voiceover lines, one per scene.
- **captions** — short Korean on-screen text, one per scene.
- **bgm_recommendation** — mood, genre, BPM range, per-scene energy curve, and
  a natural drop point.
- **sfx_cue_plan** — timed sound-effect cues at scene starts and transitions.
- **publishing_copy** — title, description, hashtags, call to action, and the
  mandatory Coupang Partners affiliate disclosure.
- **preview** *(optional)* — an `ffmpeg`-rendered 9:16 preview stitched from the
  five clips, only when `ffmpeg` is installed and the box is checked.

## Design guarantees

- **Offline by default.** Binds to localhost, makes no outbound network calls,
  and uses no AI or paid APIs. The only external process it may invoke is a
  locally installed `ffmpeg`/`ffprobe` for the optional preview.
- **Deterministic.** The same inputs always produce the same plan. The
  narrative skeleton reuses HYDRA's existing pipeline stages through the
  deterministic `MockClaudeProvider`.
- **No fabrication.** Facts the product JSON does not provide (rating, review
  count, price) are omitted from the copy — never invented.
- **Stdlib-only server.** No web framework; `http.server` plus a small
  multipart parser (`multipart.py`).

## Modules

| File | Responsibility |
| --- | --- |
| `../app.py` | Launcher: parses args, starts the server, opens the browser |
| `server.py` | HTTP handler, routing, HTML rendering, run persistence |
| `shortform_editor.py` | Deterministic, rule-based plan generator |
| `media.py` | Optional `ffmpeg`/`ffprobe` helpers (guarded, graceful) |
| `multipart.py` | Minimal `multipart/form-data` parser (stdlib only) |

Tests: `tests/webapp/` (fully offline; the server test uses a loopback socket).
