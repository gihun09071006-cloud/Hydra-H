"""Offline short-form editing plan generator (TASK-028).

Given a :class:`ProductFacts` contract (parsed from an uploaded Coupang product
JSON) and exactly five uploaded source videos, this module produces a complete,
deterministic **editing plan**:

    - video_metadata          (platform, aspect ratio, resolution, duration…)
    - source_role_assignments (which uploaded clip plays which narrative role)
    - clip_timeline           (per-scene start/end + source in/out points)
    - narration               (Korean voiceover lines, per scene)
    - captions                (Korean on-screen text, per scene)
    - bgm_recommendation      (mood, genre, tempo, per-scene energy)
    - sfx_cue_plan            (timed sound-effect cues)
    - publishing_copy         (title, description, hashtags, disclosure)

Design constraints (from TASK-028):

    * Runs locally and offline. No network calls, no AI/paid APIs.
    * Deterministic and rule-based — the same inputs always yield the same plan.
    * Never fabricates facts. Fields the product JSON does not provide (rating,
      review count, price…) are simply omitted from the copy, never invented.

The narrative skeleton (Hook → Problem → Solution → Proof → CTA) is obtained by
running HYDRA's existing offline pipeline stages through the deterministic
:class:`MockClaudeProvider`, so this module stays consistent with the rest of
the system instead of re-deriving the story structure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from contracts.product_facts import ProductFacts
from engines.creative_strategy_engine import CreativeStrategyEngine
from engines.market_fit_engine import MarketFitEngine
from engines.product_intelligence_engine import ProductIntelligenceEngine
from engines.story_engine import StoryEngine
from providers.claude.mock_claude_provider import MockClaudeProvider

# Number of source videos the app requires (TASK-028: "exactly five").
REQUIRED_VIDEO_COUNT = 5

# Vertical short-form render target.
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
TARGET_FPS = 30

# Coupang Partners affiliate disclosure (Korean). Mandatory in publishing copy.
# NOTE: this belongs to publishing/compliance output only. It is intentionally
# NEVER placed inside an AI render prompt.
COUPANG_DISCLOSURE = (
    "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."
)

# Map the pipeline's English scene goals onto stable Korean role identities.
# Each role carries the creative intent for that beat of the video.
_ROLE_BY_GOAL = {
    "Hook": {
        "role": "hook",
        "role_ko": "훅",
        "intent": "3초 안에 시선을 붙잡는다",
    },
    "Problem": {
        "role": "problem",
        "role_ko": "문제 제기",
        "intent": "시청자가 공감할 불편함을 보여준다",
    },
    "Solution": {
        "role": "solution",
        "role_ko": "해결",
        "intent": "제품을 해결책으로 제시한다",
    },
    "Proof": {
        "role": "proof",
        "role_ko": "증거",
        "intent": "효과를 눈으로 증명한다",
    },
    "CTA": {
        "role": "cta",
        "role_ko": "행동 유도",
        "intent": "지금 확인하도록 만든다",
    },
}

_DEFAULT_ROLE = {"role": "b_roll", "role_ko": "보조 장면", "intent": "장면을 보강한다"}


@dataclass
class VideoInput:
    """A single uploaded source video.

    ``duration`` is the probed length in seconds, or ``None`` when it could not
    be determined (e.g. ffprobe is unavailable). ``path`` is optional and used
    only by the preview renderer.
    """

    filename: str
    path: Optional[str] = None
    duration: Optional[float] = None


class PlanError(ValueError):
    """Raised when the inputs cannot produce a valid editing plan."""


# --------------------------------------------------------------------------- #
# Small formatting helpers (no fabrication — return None when data is absent). #
# --------------------------------------------------------------------------- #

def _clean(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _format_price(facts: ProductFacts) -> Optional[str]:
    if not isinstance(facts.price, (int, float)) or isinstance(facts.price, bool):
        return None
    amount = facts.price
    currency = (facts.currency or "").strip().upper()
    if currency in ("", "KRW", "WON", "₩"):
        return f"{amount:,.0f}원"
    return f"{amount:,.0f} {currency}"


def _short_name(facts: ProductFacts) -> str:
    name = _clean(facts.product_name) or "이 제품"
    # Keep captions punchy: trim overly long product names for on-screen text.
    if len(name) > 18:
        return name[:17].rstrip() + "…"
    return name


def _top_feature(facts: ProductFacts) -> Optional[str]:
    for feature in facts.features or []:
        text = _clean(feature)
        if text:
            return text
    return None


def _has_social_proof(facts: ProductFacts) -> bool:
    rating_ok = isinstance(facts.rating, (int, float)) and not isinstance(facts.rating, bool)
    reviews_ok = isinstance(facts.review_count, int) and not isinstance(facts.review_count, bool)
    return bool(rating_ok or reviews_ok)


def _social_proof_line(facts: ProductFacts) -> Optional[str]:
    parts = []
    if isinstance(facts.rating, (int, float)) and not isinstance(facts.rating, bool):
        parts.append(f"별점 {facts.rating:g}점")
    if isinstance(facts.review_count, int) and not isinstance(facts.review_count, bool):
        parts.append(f"리뷰 {facts.review_count:,}개")
    if not parts:
        return None
    return " · ".join(parts) + "가 증명합니다."


# --------------------------------------------------------------------------- #
# Pipeline access (deterministic, offline).                                    #
# --------------------------------------------------------------------------- #

def _run_offline_pipeline(facts: ProductFacts) -> dict[str, Any]:
    """Run the deterministic HYDRA stages to get the narrative skeleton.

    Returns the market-fit result, creative strategy, and storyboard. Uses the
    :class:`MockClaudeProvider`, so it is fully offline and reproducible.
    """
    provider = MockClaudeProvider()
    intelligence = ProductIntelligenceEngine(provider).analyze(facts)
    market_fit = MarketFitEngine().evaluate(intelligence.to_dict())
    strategy = CreativeStrategyEngine(provider).decide(intelligence, market_fit)
    storyboard = StoryEngine(provider).generate(strategy)
    return {
        "market_fit": market_fit,
        "strategy": strategy.to_dict(),
        "storyboard": storyboard.to_dict(),
    }


# --------------------------------------------------------------------------- #
# Section builders.                                                            #
# --------------------------------------------------------------------------- #

def _role_for_goal(goal: str) -> dict[str, str]:
    return _ROLE_BY_GOAL.get(goal, _DEFAULT_ROLE)


def _source_role_assignments(
    scenes: list[dict[str, Any]], videos: list[VideoInput]
) -> list[dict[str, Any]]:
    """Assign each uploaded clip to a scene role, in upload order.

    Assignment is deterministic (upload order → scene order). The plan documents
    that the user can reorder assignments in the UI.
    """
    assignments = []
    for index, (scene, video) in enumerate(zip(scenes, videos), start=1):
        role = _role_for_goal(scene.get("goal", ""))
        assignments.append(
            {
                "slot": index,
                "scene": scene.get("scene", index),
                "role": role["role"],
                "role_ko": role["role_ko"],
                "intent": role["intent"],
                "source_video": video.filename,
                "source_duration_sec": (
                    round(video.duration, 3) if video.duration is not None else None
                ),
                "assignment_basis": "업로드 순서 기반 기본 배정 (UI에서 변경 가능)",
            }
        )
    return assignments


def _clip_timeline(
    scenes: list[dict[str, Any]], videos: list[VideoInput]
) -> list[dict[str, Any]]:
    """Build the per-scene timeline with playhead times and source in/out points.

    Each scene uses ``scene.duration`` seconds of footage taken from the start
    of its assigned source clip. When the source is shorter than the scene, the
    plan flags it so the editor knows to loop, slow-mo, or trim the scene.
    """
    timeline = []
    playhead = 0.0
    transitions = ["cut", "whip_pan", "cut", "zoom", "cut"]
    for index, (scene, video) in enumerate(zip(scenes, videos)):
        scene_len = float(scene.get("duration", 0) or 0)
        start = round(playhead, 3)
        end = round(playhead + scene_len, 3)
        source_out = scene_len
        note = None
        if video.duration is not None and video.duration < scene_len:
            source_out = round(video.duration, 3)
            note = (
                f"소스가 장면보다 짧습니다 ({video.duration:g}s < {scene_len:g}s). "
                "루프/슬로모/장면 단축이 필요합니다."
            )
        timeline.append(
            {
                "scene": scene.get("scene", index + 1),
                "role": _role_for_goal(scene.get("goal", ""))["role"],
                "timeline_start_sec": start,
                "timeline_end_sec": end,
                "duration_sec": round(scene_len, 3),
                "source_video": video.filename,
                "source_in_sec": 0.0,
                "source_out_sec": round(source_out, 3),
                "transition_out": transitions[index % len(transitions)],
                "note": note,
            }
        )
        playhead = end
    return timeline


def _narration(scenes: list[dict[str, Any]], facts: ProductFacts) -> list[dict[str, Any]]:
    """Korean voiceover lines, one per scene, built from real product facts."""
    name = _clean(facts.product_name) or "이 제품"
    price = _format_price(facts)
    feature = _top_feature(facts)
    proof = _social_proof_line(facts)

    lines_by_role = {
        "hook": f"{name}, 아직도 그냥 참고 계셨어요?",
        "problem": "매일 반복되는 이 불편함, 익숙하시죠.",
        "solution": (
            f"{name} 하나면 이렇게 간단하게 해결됩니다."
            if not feature
            else f"{name}, {feature} 하나로 끝냅니다."
        ),
        "proof": proof or "직접 써보면 차이가 바로 느껴집니다.",
        "cta": (
            f"지금 링크에서 확인하세요. {price}."
            if price
            else "지금 링크에서 확인해 보세요."
        ),
    }

    narration = []
    for index, scene in enumerate(scenes, start=1):
        role = _role_for_goal(scene.get("goal", ""))["role"]
        text = lines_by_role.get(role, f"{name}의 장점을 보여줍니다.")
        narration.append(
            {
                "scene": scene.get("scene", index),
                "role": role,
                "language": "ko",
                "text": text,
                "tone": "친근하고 확신에 찬",
            }
        )
    return narration


def _captions(scenes: list[dict[str, Any]], facts: ProductFacts) -> list[dict[str, Any]]:
    """Short Korean on-screen captions (punchy, one line each)."""
    name = _short_name(facts)
    feature = _top_feature(facts)
    price = _format_price(facts)

    caption_by_role = {
        "hook": "이거 실화?",
        "problem": "매번 이 고생…",
        "solution": (feature or f"{name} 하나면 끝"),
        "proof": "직접 보세요 👀",
        "cta": (price and f"지금 {price}") or "지금 확인 ↓",
    }

    captions = []
    for index, scene in enumerate(scenes, start=1):
        role = _role_for_goal(scene.get("goal", ""))["role"]
        text = caption_by_role.get(role, name)
        captions.append(
            {
                "scene": scene.get("scene", index),
                "role": role,
                "language": "ko",
                "text": text,
                "position": "center" if role in ("hook", "cta") else "lower_third",
                "style": "bold",
            }
        )
    return captions


# Strategy → BGM mood mapping (deterministic).
_BGM_BY_STRATEGY = {
    "Visual Demonstration": {
        "mood": "밝고 경쾌한",
        "genre": "Upbeat Pop / Corporate",
        "bpm_range": [110, 128],
    },
    "Problem-Solution": {
        "mood": "긴장에서 해소로",
        "genre": "Cinematic Pop",
        "bpm_range": [95, 115],
    },
    "Storytelling": {
        "mood": "따뜻하고 감성적인",
        "genre": "Acoustic / Lo-fi",
        "bpm_range": [80, 100],
    },
}

_DEFAULT_BGM = {
    "mood": "밝고 경쾌한",
    "genre": "Upbeat Pop",
    "bpm_range": [100, 120],
}


def _bgm_recommendation(
    scenes: list[dict[str, Any]], strategy: dict[str, Any]
) -> dict[str, Any]:
    base = _BGM_BY_STRATEGY.get(strategy.get("strategy", ""), _DEFAULT_BGM)
    energy_by_role = {
        "hook": "high",
        "problem": "low",
        "solution": "rising",
        "proof": "high",
        "cta": "peak",
    }
    energy_curve = []
    for index, scene in enumerate(scenes, start=1):
        role = _role_for_goal(scene.get("goal", ""))["role"]
        energy_curve.append(
            {
                "scene": scene.get("scene", index),
                "role": role,
                "energy": energy_by_role.get(role, "medium"),
            }
        )
    return {
        "mood": base["mood"],
        "genre": base["genre"],
        "bpm_range": base["bpm_range"],
        "energy_curve": energy_curve,
        "drop_at_sec": _drop_time(scenes),
        "license_note": "저작권 문제가 없는 로열티 프리 음원 사용을 권장합니다.",
    }


def _drop_time(scenes: list[dict[str, Any]]) -> Optional[float]:
    """Return the timeline time where the Solution beat begins (a natural drop)."""
    playhead = 0.0
    for scene in scenes:
        role = _role_for_goal(scene.get("goal", ""))["role"]
        if role == "solution":
            return round(playhead, 3)
        playhead += float(scene.get("duration", 0) or 0)
    return None


def _sfx_cue_plan(scenes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Timed sound-effect cues aligned to scene boundaries and key beats."""
    sfx_by_role = {
        "hook": "impact_boom",
        "problem": "tension_riser",
        "solution": "sparkle_pop",
        "proof": "confirm_ding",
        "cta": "notification_tap",
    }
    cues = []
    playhead = 0.0
    for index, scene in enumerate(scenes, start=1):
        role = _role_for_goal(scene.get("goal", ""))["role"]
        cues.append(
            {
                "at_sec": round(playhead, 3),
                "scene": scene.get("scene", index),
                "role": role,
                "sfx": sfx_by_role.get(role, "whoosh"),
                "purpose": "장면 시작 강조",
            }
        )
        # Add a transition whoosh at the boundary into the next scene.
        playhead += float(scene.get("duration", 0) or 0)
        if index < len(scenes):
            cues.append(
                {
                    "at_sec": round(playhead, 3),
                    "scene": scene.get("scene", index),
                    "role": "transition",
                    "sfx": "swipe_whoosh",
                    "purpose": "장면 전환",
                }
            )
    return cues


def _hashtags(facts: ProductFacts) -> list[str]:
    tags = ["#쿠팡", "#쿠팡추천", "#가성비", "#꿀템", "#쇼츠"]
    category = _clean(facts.category)
    if category:
        tags.insert(0, "#" + category.replace(" ", ""))
    return tags[:8]


def _publishing_copy(
    facts: ProductFacts, total_duration: float, market_fit: dict[str, Any]
) -> dict[str, Any]:
    name = _clean(facts.product_name) or "추천 상품"
    price = _format_price(facts)
    feature = _top_feature(facts)

    title_bits = [name]
    if feature:
        title_bits.append(feature)
    title = " | ".join(title_bits)
    if len(title) > 40:
        title = title[:39].rstrip() + "…"

    desc_lines = [f"{name} 리뷰 & 사용법을 {int(round(total_duration))}초에 정리했습니다."]
    if feature:
        desc_lines.append(f"핵심 포인트: {feature}")
    if price:
        desc_lines.append(f"가격: {price}")
    if facts.affiliate_url or facts.source_url:
        desc_lines.append(f"구매 링크: {facts.affiliate_url or facts.source_url}")

    return {
        "title": title,
        "description": "\n".join(desc_lines),
        "hashtags": _hashtags(facts),
        "affiliate_disclosure": COUPANG_DISCLOSURE,
        "call_to_action": "프로필/댓글의 링크에서 확인하세요.",
        "advertising_decision": market_fit.get("decision"),
    }


def _video_metadata(
    facts: ProductFacts, total_duration: float, strategy: dict[str, Any]
) -> dict[str, Any]:
    name = _clean(facts.product_name) or "제품 쇼츠"
    return {
        "title": f"{name} 쇼츠",
        "language": "ko",
        "orientation": "vertical",
        "aspect_ratio": "9:16",
        "resolution": f"{TARGET_WIDTH}x{TARGET_HEIGHT}",
        "fps": TARGET_FPS,
        "total_duration_sec": round(total_duration, 3),
        "scene_count": len(strategy.get("storyboard_scenes", []) or []),
        "strategy": strategy.get("strategy"),
        "story_pattern": strategy.get("story_pattern"),
        "source_marketplace": facts.marketplace or "coupang",
        "product_url": facts.source_url,
        "affiliate_url": facts.affiliate_url,
    }


# --------------------------------------------------------------------------- #
# Public API.                                                                  #
# --------------------------------------------------------------------------- #

def build_plan(
    facts: ProductFacts,
    videos: list[VideoInput],
    *,
    require_five: bool = True,
) -> dict[str, Any]:
    """Produce the complete editing plan (pure, deterministic, offline).

    Args:
        facts: parsed product facts (never fabricated downstream).
        videos: the uploaded source clips, in upload order.
        require_five: enforce the TASK-028 "exactly five videos" rule.

    Raises:
        PlanError: when the inputs are invalid.
    """
    if not isinstance(facts, ProductFacts):
        raise PlanError("facts must be a ProductFacts instance")
    if not _clean(facts.product_name):
        raise PlanError("product JSON is missing 'product_name'")
    if not isinstance(videos, list) or not all(isinstance(v, VideoInput) for v in videos):
        raise PlanError("videos must be a list of VideoInput")
    if require_five and len(videos) != REQUIRED_VIDEO_COUNT:
        raise PlanError(
            f"exactly {REQUIRED_VIDEO_COUNT} source videos are required "
            f"(got {len(videos)})"
        )
    if not videos:
        raise PlanError("at least one source video is required")

    pipeline = _run_offline_pipeline(facts)
    strategy = pipeline["strategy"]
    market_fit = pipeline["market_fit"]
    scenes = pipeline["storyboard"].get("scenes") or []
    if not scenes:
        raise PlanError("storyboard produced no scenes")

    # Map videos onto scenes. With five scenes and five videos this is 1:1;
    # otherwise videos are distributed across scenes by index.
    paired_videos = [videos[min(i, len(videos) - 1)] for i in range(len(scenes))]

    total_duration = float(pipeline["storyboard"].get("duration", 0) or 0)
    if total_duration <= 0:
        total_duration = sum(float(s.get("duration", 0) or 0) for s in scenes)

    strategy_for_meta = dict(strategy)
    strategy_for_meta["storyboard_scenes"] = scenes

    return {
        "schema_version": "1.0",
        "generator": "HYDRA Local Web App (offline)",
        "product": {
            "product_name": facts.product_name,
            "price": facts.price,
            "currency": facts.currency,
            "marketplace": facts.marketplace,
            "source_url": facts.source_url,
            "affiliate_url": facts.affiliate_url,
        },
        "video_metadata": _video_metadata(facts, total_duration, strategy_for_meta),
        "source_role_assignments": _source_role_assignments(scenes, paired_videos),
        "clip_timeline": _clip_timeline(scenes, paired_videos),
        "narration": _narration(scenes, facts),
        "captions": _captions(scenes, facts),
        "bgm_recommendation": _bgm_recommendation(scenes, strategy),
        "sfx_cue_plan": _sfx_cue_plan(scenes),
        "publishing_copy": _publishing_copy(facts, total_duration, market_fit),
        "market_fit": {
            "score": market_fit.get("market_fit_score"),
            "decision": market_fit.get("decision"),
        },
    }


def probe_videos(
    videos: list[VideoInput],
    duration_fn: Optional[Callable[[str], Optional[float]]] = None,
) -> list[VideoInput]:
    """Return copies of ``videos`` with durations filled in via ``duration_fn``.

    ``duration_fn`` maps a path to seconds (or ``None``). When it is not
    supplied or a clip has no path, the duration is left as ``None``. This keeps
    duration probing (which may shell out to ffprobe) injectable and testable.
    """
    if duration_fn is None:
        return list(videos)
    probed = []
    for video in videos:
        duration = video.duration
        if duration is None and video.path:
            try:
                duration = duration_fn(video.path)
            except Exception:
                duration = None
        probed.append(VideoInput(filename=video.filename, path=video.path, duration=duration))
    return probed
