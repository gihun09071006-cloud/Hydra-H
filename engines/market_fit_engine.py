"""Executable Market Fit Engine for HYDRA.

Implements the specification in ``system/MARKET_FIT_ENGINE.md``. The engine
consumes a Product Intelligence object
(``data/schemas/product_intelligence.schema.json``) and returns a Market Fit
object (``data/schemas/market_fit.schema.json``).

It never generates advertisements: it scores advertising viability across ten
weighted categories, every score carries a written reason, and the total maps to
a decision tier. The scoring rules below are deterministic v1 heuristics over the
canonical Product Intelligence fields; they are extensible without changing the
input or output contracts.
"""

from __future__ import annotations

from typing import Any

# Category -> maximum score. The maximums sum to 100.
CATEGORY_MAX: dict[str, int] = {
    "Visual Demonstration": 20,
    "Problem Severity": 15,
    "Emotional Appeal": 10,
    "Impulse Buying": 10,
    "Price Advantage": 10,
    "Novelty": 10,
    "Competition": 10,
    "Trust": 5,
    "Creative Diversity": 5,
    "Viral Potential": 5,
}

# Recommendation mappings, keyed by the strongest category. Values align with the
# Creative Strategy Engine's strategy and hook vocabularies.
STRATEGY_BY_CATEGORY: dict[str, str] = {
    "Visual Demonstration": "Visual Demonstration",
    "Problem Severity": "Problem → Solution",
    "Emotional Appeal": "Emotional Story",
    "Impulse Buying": "Lifestyle",
    "Price Advantage": "Comparison",
    "Novelty": "Visual Demonstration",
    "Competition": "Comparison",
    "Trust": "Social Proof",
    "Creative Diversity": "UGC Review",
    "Viral Potential": "POV",
}

HOOK_BY_CATEGORY: dict[str, str] = {
    "Visual Demonstration": "Demonstration",
    "Problem Severity": "Question",
    "Emotional Appeal": "Transformation",
    "Impulse Buying": "Curiosity",
    "Price Advantage": "Contrarian",
    "Novelty": "Shock",
    "Competition": "Contrarian",
    "Trust": "Authority",
    "Creative Diversity": "Curiosity",
    "Viral Potential": "Curiosity",
}


def _round_half_up(value: float) -> int:
    """Round a non-negative value half-up to the nearest integer."""
    return int(value + 0.5)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _scale(signal: float, maximum: int) -> int:
    """Scale a 0-100 signal onto ``0..maximum`` (half-up)."""
    return _round_half_up(_clamp(signal, 0, 100) / 100.0 * maximum)


def _mean(*values: float) -> float:
    return sum(values) / len(values) if values else 0.0


def decide(market_fit_score: int) -> str:
    """Map a Market Fit score (0-100) to its decision tier."""
    if market_fit_score >= 90:
        return "Create Immediately"
    if market_fit_score >= 80:
        return "Priority A"
    if market_fit_score >= 70:
        return "Priority B"
    if market_fit_score >= 60:
        return "Optional"
    return "Reject"


DECISION_ACTION: dict[str, str] = {
    "Create Immediately": "Create immediately",
    "Priority A": "Create immediately",
    "Priority B": "Create if resources allow",
    "Optional": "Create if resources allow",
    "Reject": "Do not create",
}


class MarketFitEngine:
    """Scores a Product Intelligence object for advertising viability."""

    def evaluate(self, product_intelligence: dict[str, Any]) -> dict[str, Any]:
        """Return a Market Fit object for ``product_intelligence``."""
        pi = product_intelligence
        scored = self._score_categories(pi)

        market_fit_score = int(_clamp(sum(c["score"] for c in scored), 0, 100))
        decision = decide(market_fit_score)

        # Rank by normalized ratio (score / max); ties keep canonical order.
        ranked = sorted(
            enumerate(scored), key=lambda p: (-p[1]["ratio"], p[0])
        )
        strengths = [self._public(scored[i]) for i, _ in ranked[:3]]
        weakest = sorted(enumerate(scored), key=lambda p: (p[1]["ratio"], p[0]))
        weaknesses = [self._public(scored[i]) for i, _ in weakest[:3]]

        top_category = scored[ranked[0][0]]["category"]

        return {
            "market_fit_score": market_fit_score,
            "decision": decision,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommended_strategy": STRATEGY_BY_CATEGORY[top_category],
            "recommended_hook_type": HOOK_BY_CATEGORY[top_category],
            "confidence": self._confidence(pi, market_fit_score),
        }

    # -- scoring ------------------------------------------------------------

    def _score_categories(self, pi: dict[str, Any]) -> list[dict[str, Any]]:
        va = pi["visual_analysis"]
        vir = pi["virality_analysis"]
        comp = pi["competitive_analysis"]
        fa = pi["functional_analysis"]

        vis = va["visual_proof_strength"]
        pains = pi["pain_analysis"]
        pain_max = max((p["severity"] for p in pains), default=0)
        top_pain = min(pains, key=lambda p: p["rank"])["problem"] if pains else "none"
        objs = pi["objection_analysis"]
        obj_max = max((o["probability"] for o in objs), default=0)
        alt_count = len(comp["existing_alternatives"])

        results: list[dict[str, Any]] = []

        # 1. Visual Demonstration
        signal = vis
        if va["before_after_possible"]:
            signal += 5
        if va["transformation_possible"]:
            signal += 5
        signal = min(signal, 100)
        if not va["benefit_visually_demonstrable"]:
            signal *= 0.5
        results.append(self._cat(
            "Visual Demonstration", signal,
            f"Visual proof strength {vis}/100; demonstrable="
            f"{va['benefit_visually_demonstrable']}, before/after="
            f"{va['before_after_possible']}, transformation="
            f"{va['transformation_possible']}.",
        ))

        # 2. Problem Severity
        results.append(self._cat(
            "Problem Severity", pain_max,
            f"Top pain '{top_pain}' has severity {pain_max}/100.",
        ))

        # 3. Emotional Appeal (proxied by virality surprise + satisfaction, since
        #    Product Intelligence expresses emotion qualitatively).
        emo = _mean(vir["surprise_potential"], vir["satisfaction_potential"])
        results.append(self._cat(
            "Emotional Appeal", emo,
            f"Emotional resonance proxied by surprise {vir['surprise_potential']}"
            f" and satisfaction {vir['satisfaction_potential']} (avg {emo:.0f}).",
        ))

        # 4. Impulse Buying (fast, low-friction appeal)
        imp = _mean(vir["scroll_stop_potential"], vis)
        results.append(self._cat(
            "Impulse Buying", imp,
            f"Impulse proxied by scroll-stop {vir['scroll_stop_potential']} and"
            f" visual proof {vis} (avg {imp:.0f}).",
        ))

        # 5. Price Advantage (edge over pricier/effortful alternatives)
        price_signal = (
            30 * bool(comp["offline_alternative"].strip())
            + 30 * bool(comp["diy_alternative"].strip())
            + 40 * bool(comp["why_buy_this_instead"].strip())
        )
        results.append(self._cat(
            "Price Advantage", price_signal,
            "Advantage over offline/DIY alternatives and stated reason to buy"
            f" (signal {min(price_signal, 100)}/100).",
        ))

        # 6. Novelty
        results.append(self._cat(
            "Novelty", vir["surprise_potential"],
            f"Novelty proxied by surprise potential {vir['surprise_potential']}/100.",
        ))

        # 7. Competition (favorable when few alternatives)
        comp_signal = max(0, 100 - 25 * alt_count)
        results.append(self._cat(
            "Competition", comp_signal,
            f"{alt_count} existing alternative(s); competitive favorability"
            f" {comp_signal}/100.",
        ))

        # 8. Trust (higher when objections are weak)
        results.append(self._cat(
            "Trust", 100 - obj_max,
            f"Strongest objection probability {obj_max}/100; trust signal"
            f" {100 - obj_max}/100.",
        ))

        # 9. Creative Diversity (distinct angles available)
        count = (
            len(fa["secondary_functions"]) + len(fa["top_features"])
            + int(va["before_after_possible"]) + int(va["transformation_possible"])
        )
        div = min(100, count * 15)
        results.append(self._cat(
            "Creative Diversity", div,
            f"{count} distinct creative angle(s) available; diversity signal"
            f" {div}/100.",
        ))

        # 10. Viral Potential
        viral = _mean(
            vir["scroll_stop_potential"], vir["surprise_potential"],
            vir["satisfaction_potential"], vir["shareability"],
            vir["comment_potential"],
        )
        results.append(self._cat(
            "Viral Potential", viral,
            f"Average virality across five dimensions is {viral:.0f}/100.",
        ))

        return results

    def _cat(self, category: str, signal: float, reason: str) -> dict[str, Any]:
        maximum = CATEGORY_MAX[category]
        score = _scale(signal, maximum)
        return {
            "category": category,
            "score": score,
            "reason": reason,
            "max": maximum,
            "ratio": score / maximum,
        }

    @staticmethod
    def _public(cat: dict[str, Any]) -> dict[str, Any]:
        """Project a scored category onto the schema's {category, score, reason}."""
        return {
            "category": cat["category"],
            "score": cat["score"],
            "reason": cat["reason"],
        }

    def _confidence(self, pi: dict[str, Any], score: int) -> int:
        """Confidence from input completeness and decisive tier placement."""
        checks = [
            bool(pi["pain_analysis"]),
            bool(pi["objection_analysis"]),
            bool(pi["competitive_analysis"]["existing_alternatives"]),
            bool(pi["functional_analysis"]["secondary_functions"]),
            bool(pi["customer_analysis"]["emotional_motivation"].strip()),
        ]
        completeness = sum(checks) / len(checks)
        boundaries = (60, 70, 80, 90)
        dist = min(abs(score - b) for b in boundaries)
        confidence = 55 + completeness * 30 + min(dist, 15)
        return int(_clamp(_round_half_up(confidence), 0, 100))


def evaluate(product_intelligence: dict[str, Any]) -> dict[str, Any]:
    """Convenience wrapper around :meth:`MarketFitEngine.evaluate`."""
    return MarketFitEngine().evaluate(product_intelligence)
