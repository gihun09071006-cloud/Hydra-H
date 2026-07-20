# HYDRA Market Fit Engine — Specification

## Purpose

Evaluate whether a product deserves creative production.

Before HYDRA creates any advertisement, the Market Fit Engine determines whether
the product is worth advertising at all. The engine outputs a **Market Fit
Score** *before any advertisement is generated*. A rejected product never
proceeds to creative production.

This document is a specification only. It defines the engine's inputs, output,
scoring, and decision rules. It contains **no business logic, no AI prompt
implementation, and no code**.

---

## Input

**Product Intelligence JSON** — the Product Intelligence Record produced by the
Product Intelligence Engine (`PRODUCT_INTELLIGENCE_ENGINE.md`).

---

## Output

```json
{
  "market_fit_score": 0,
  "decision": "",
  "strengths": [],
  "weaknesses": [],
  "recommended_strategy": "",
  "recommended_hook_type": "",
  "confidence": 0
}
```

- `market_fit_score` — integer 0–100, the weighted total of the scoring
  categories below.
- `decision` — one of the decision tiers (see **Decision Rules**).
- `strengths` — the product's strongest scoring categories, each with a reason.
- `weaknesses` — the product's weakest scoring categories, each with a reason.
- `recommended_strategy` — the marketing strategy the evidence points to.
- `recommended_hook_type` — the hook type the evidence points to.
- `confidence` — integer 0–100, how confident the evaluation is.

---

## Scoring Categories

Each category is scored up to its maximum. The maximums sum to **100**.

| Category | Max Score |
|-----------|----------:|
| Visual Demonstration | 20 |
| Problem Severity | 15 |
| Emotional Appeal | 10 |
| Impulse Buying | 10 |
| Price Advantage | 10 |
| Novelty | 10 |
| Competition | 10 |
| Trust | 5 |
| Creative Diversity | 5 |
| Viral Potential | 5 |
| **Total** | **100** |

---

## Decision Rules

The `market_fit_score` maps to exactly one decision tier:

| Score | Decision |
|-------|----------|
| 90–100 | Create Immediately |
| 80–89 | Priority A |
| 70–79 | Priority B |
| 60–69 | Optional |
| Below 60 | Reject |

---

## Transparency Rules

- **Every score must contain a written reason.** No category is scored without a
  stated justification.
- **No hidden reasoning.** The rationale behind every score is explicit and
  inspectable.
- **Every recommendation must include evidence.** The `decision`,
  `recommended_strategy`, and `recommended_hook_type` are each backed by the
  scored evidence that produced them.

---

## Scope Boundary

| In scope | Out of scope |
| --- | --- |
| Scoring advertising viability | Generating advertisements |
| Weighted, reasoned category scores | Generating prompts or creative |
| Producing a Market Fit Score + decision | Deciding final creative direction |
| Gating the pipeline before creative | Rendering or delivery |
