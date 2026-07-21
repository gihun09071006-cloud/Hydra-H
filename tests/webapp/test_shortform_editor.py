"""Offline tests for the short-form editing plan generator (TASK-028)."""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from contracts.product_facts import ProductFacts  # noqa: E402
from webapp.shortform_editor import (  # noqa: E402
    COUPANG_DISCLOSURE,
    REQUIRED_VIDEO_COUNT,
    PlanError,
    VideoInput,
    build_plan,
    probe_videos,
)


def _facts(**overrides):
    base = dict(
        product_name="무선 목 어깨 마사지기",
        price=39900,
        currency="KRW",
        features=["무선 착용형", "온열 기능", "강도 조절"],
        rating=4.7,
        review_count=1234,
        marketplace="coupang",
        source_url="https://www.coupang.com/vp/products/1",
        affiliate_url="https://link.coupang.com/a/abc",
    )
    base.update(overrides)
    return ProductFacts(**base)


def _videos(n=REQUIRED_VIDEO_COUNT, duration=None):
    return [VideoInput(filename=f"clip{i}.mp4", path=f"/tmp/clip{i}.mp4", duration=duration)
            for i in range(1, n + 1)]


def test_build_plan_has_all_sections():
    plan = build_plan(_facts(), _videos())
    for key in (
        "video_metadata",
        "source_role_assignments",
        "clip_timeline",
        "narration",
        "captions",
        "bgm_recommendation",
        "sfx_cue_plan",
        "publishing_copy",
    ):
        assert key in plan, f"missing section: {key}"


def test_exactly_five_videos_required():
    with pytest.raises(PlanError):
        build_plan(_facts(), _videos(4))
    with pytest.raises(PlanError):
        build_plan(_facts(), _videos(6))


def test_require_five_can_be_relaxed():
    plan = build_plan(_facts(), _videos(3), require_five=False)
    assert plan["clip_timeline"]  # still produces a plan


def test_missing_product_name_rejected():
    with pytest.raises(PlanError):
        build_plan(_facts(product_name=None), _videos())


def test_role_assignments_follow_upload_order():
    plan = build_plan(_facts(), _videos())
    roles = [a["role"] for a in plan["source_role_assignments"]]
    assert roles == ["hook", "problem", "solution", "proof", "cta"]
    sources = [a["source_video"] for a in plan["source_role_assignments"]]
    assert sources == [f"clip{i}.mp4" for i in range(1, 6)]


def test_timeline_is_contiguous_and_ordered():
    plan = build_plan(_facts(), _videos())
    timeline = plan["clip_timeline"]
    assert timeline[0]["timeline_start_sec"] == 0.0
    for prev, nxt in zip(timeline, timeline[1:]):
        assert prev["timeline_end_sec"] == nxt["timeline_start_sec"]
    total = plan["video_metadata"]["total_duration_sec"]
    assert timeline[-1]["timeline_end_sec"] == total


def test_narration_and_captions_are_korean_and_per_scene():
    plan = build_plan(_facts(), _videos())
    assert len(plan["narration"]) == 5
    assert len(plan["captions"]) == 5
    assert all(n["language"] == "ko" for n in plan["narration"])
    # Price appears in the CTA narration when available.
    cta = next(n for n in plan["narration"] if n["role"] == "cta")
    assert "39,900원" in cta["text"]


def test_no_fabrication_when_facts_absent():
    plan = build_plan(_facts(rating=None, review_count=None, price=None), _videos())
    proof = next(n for n in plan["narration"] if n["role"] == "proof")
    # Falls back to a generic line — never invents a rating/review count.
    assert "별점" not in proof["text"]
    assert "리뷰" not in proof["text"]
    cta = next(n for n in plan["narration"] if n["role"] == "cta")
    assert "원" not in cta["text"] or "링크" in cta["text"]


def test_publishing_copy_includes_exact_disclosure():
    plan = build_plan(_facts(), _videos())
    assert plan["publishing_copy"]["affiliate_disclosure"] == COUPANG_DISCLOSURE


def test_deterministic_output():
    a = build_plan(_facts(), _videos())
    b = build_plan(_facts(), _videos())
    assert a == b


def test_short_source_is_flagged_in_timeline():
    # A 1-second source under a multi-second scene should be flagged.
    videos = _videos(duration=1.0)
    plan = build_plan(_facts(), videos)
    flagged = [s for s in plan["clip_timeline"] if s["note"]]
    assert flagged, "expected at least one short-source note"


def test_bgm_and_sfx_present_per_scene():
    plan = build_plan(_facts(), _videos())
    assert len(plan["bgm_recommendation"]["energy_curve"]) == 5
    sfx_roles = {c["role"] for c in plan["sfx_cue_plan"]}
    assert "transition" in sfx_roles  # transition cues between scenes


def test_probe_videos_fills_durations():
    videos = _videos()
    probed = probe_videos(videos, duration_fn=lambda path: 12.5)
    assert all(v.duration == 12.5 for v in probed)


def test_probe_videos_without_fn_is_noop():
    videos = _videos()
    probed = probe_videos(videos, duration_fn=None)
    assert all(v.duration is None for v in probed)
