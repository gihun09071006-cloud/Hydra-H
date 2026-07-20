# HYDRA Market Fit Scoring Engine — Specification

The **Market Fit Scoring Engine** decides whether a product is worth creating
advertisements for **before any creative asset is generated**. It is a go/no-go
gate: it scores a product's advertising potential, ranks its strengths and
weaknesses, and returns a clear recommendation.

> **Core principle — qualify before you create.**
> This engine never generates creative. It estimates advertising viability so
> that effort is spent only on products likely to perform.

The engine is **rule-based**: every dimension is scored on a fixed, deterministic
scale and the total is derived transparently. Identical inputs always produce the
same Market Fit result.

---

## 1. Position in the Pipeline

```
Product Intelligence Engine  ──►  Market Fit Scoring Engine  ──►  Decision Engine
(understand the product)          (is it worth advertising?)      (decide the creative)
                                          │
                                   Reject ┴─►  stop (do not create)
```

The Market Fit Scoring Engine consumes the Product Intelligence Record (from
`PRODUCT_INTELLIGENCE_ENGINE.md`) and acts as a gate. A `Reject` result stops the
campaign before the Decision Engine is ever invoked. In state-machine terms this
gate sits between `PRODUCT_ANALYZED` and `STRATEGY_SELECTED`.

---

## 2. Scoring Model

- **Scale.** Every dimension is scored as an integer **0–100** (higher = more
  favorable for advertising). This matches the score scale used across HYDRA.
- **Total.** The **Market Fit Score (0–100)** is the weighted aggregate of the
  ten dimension scores, rounded to an integer. Default weighting is **equal**
  (each dimension 10%); weights are configuration, not part of this contract.
- **Deterministic.** Given the same dimension scores and weights, the total is
  always the same.

### 2.1 Scoring Dimensions

All ten dimensions are scored 0–100, where **100 is most favorable for
advertising**.

| Dimension | 100 (favorable) means… |
| --- | --- |
| **Visual Demonstration** | The benefit is easy to show on screen. |
| **Problem Severity** | It solves a painful, high-stakes problem. |
| **Emotional Appeal** | It evokes a strong emotional response. |
| **Impulse Purchase Potential** | It invites a fast, low-friction buy. |
| **Price Advantage** | Its price is a clear advantage vs. alternatives. |
| **Novelty** | It is new, surprising, or rarely seen. |
| **Scroll Stop Potential** | It can stop the scroll in the first seconds. |
| **Viral Potential** | It is likely to be shared and spread. |
| **Competition Difficulty** | Competition is *low* — i.e. this dimension is scored **inversely**: a market that is easy to compete in scores high, a crowded/hard market scores low. |
| **Creative Diversity** | Many distinct creative angles are possible. |

> **Note on Competition Difficulty.** Higher real-world difficulty is *worse* for
> market fit. To keep the total a simple "higher = better" aggregate, this
> dimension records **competitive favorability** (100 = low difficulty / easy to
> compete, 0 = extremely hard). The underlying raw difficulty may be retained
> alongside for transparency.

---

## 3. Return Contract

The engine returns the following, and only the following:

| Field | Type | Description |
| --- | --- | --- |
| **Total Score** | integer (0–100) | The overall Market Fit Score. |
| **Dimension Scores** | 10 × integer (0–100) | Each dimension's score. |
| **Top 3 Strengths** | 3 × dimension | The three highest-scoring dimensions. |
| **Top 3 Weaknesses** | 3 × dimension | The three lowest-scoring dimensions. |
| **Recommendation** | object | Priority tier + action + rationale (see §4). |

- **Top 3 Strengths / Weaknesses** are derived directly from the dimension
  scores (highest three and lowest three). Ties are broken by the dimension
  order listed in §2.1.

---

## 4. Decision Rule

The Total Score maps to exactly one recommendation tier:

| Total Score | Priority | Action |
| --- | --- | --- |
| **80–100** | **Priority A** | Create immediately. |
| **60–79** | **Priority B** | Create if resources allow. |
| **0–59** | **Reject** | Do not create. |

The recommendation MUST include:

- **Priority** — one of `Priority A`, `Priority B`, `Reject`.
- **Action** — the corresponding action from the table above.
- **Rationale** — grounded in the Top Strengths and Weaknesses (why this tier).

A `Reject` result terminates the pipeline for this product; no creative is
generated.

---

## 5. Output Formats

- **Markdown** — this document is the human-readable specification and rule set.
- **JSON** — the machine-readable return contract is
  `data/schemas/market_fit.schema.json`; every Market Fit result validates
  against it.

---

## 6. Scope Boundary

| In scope | Out of scope |
| --- | --- |
| Estimating advertising viability | Generating advertisements |
| Deterministic 0–100 dimension scoring | Generating prompts or creative |
| Producing a total score + recommendation | Deciding creative direction |
| Gating the pipeline (A / B / Reject) | Rendering or delivery |
