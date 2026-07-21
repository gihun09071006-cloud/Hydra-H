# HYDRA Creative Strategy Engine (CSE) — Specification

## Purpose

The **Creative Strategy Engine (CSE)** selects the single best advertising
strategy for a product. It receives the Product Intelligence Record and the
Market Fit Result, weighs the available strategies, and commits to **one**
strategy — together with the hook type, story pattern, and CTA style that
express it.

The CSE decides *which creative direction to take*. It does **not** generate
advertisements, write prompts, or implement business logic. This document is a
specification only.

### Relationship to existing engines (no duplicate architecture)

The CSE does not duplicate any existing specification. It sits between analysis
and creation, and realizes specific State Machine states:

| Concern | Owner |
| --- | --- |
| Understanding the product | Product Intelligence Engine (`PRODUCT_INTELLIGENCE_ENGINE.md`) |
| Deciding whether to advertise at all | Market Fit Engine (`MARKET_FIT_ENGINE.md`) |
| **Selecting the one creative strategy (+ hook, story, CTA)** | **Creative Strategy Engine (this doc)** |
| The broader decision method / audit structure | Decision Engine (`DECISION_ENGINE.md`) |

The CSE **realizes** the State Machine's `STRATEGY_SELECTED` and `HOOK_SELECTED`
states and produces the `story_pattern` that seeds `STORY_CREATED`. It reuses the
Market Fit Engine's `recommended_strategy` / `recommended_hook_type` as priors
rather than redefining them.

---

## Inputs

### Input 1 — Product Intelligence JSON

The canonical Product Intelligence Record
(`data/schemas/product_intelligence.schema.json`, documented in
`docs/PRODUCT_INTELLIGENCE.md`).

### Input 2 — Market Fit Result

The Market Fit Engine output (`system/MARKET_FIT_ENGINE.md`), including its
`decision`, `recommended_strategy`, `recommended_hook_type`, category scores, and
`confidence`.

> **Gating.** The CSE runs only when the Market Fit `decision` is **not**
> `Reject`. A rejected product never reaches strategy selection.

---

## Outputs

The engine emits exactly this object:

```json
{
  "strategy": "",
  "reason": "",
  "confidence": 0,
  "hook_type": "",
  "story_pattern": "",
  "cta_style": ""
}
```

| Field | Type | Description |
| --- | --- | --- |
| `strategy` | enum | The single selected strategy (see **Available Strategies**). |
| `reason` | string | Full reasoning — see **Decision Rules**. No hidden reasoning. |
| `confidence` | integer (0–100) | Confidence in the selection. |
| `hook_type` | enum | One hook category (see **Hook Selection**). |
| `story_pattern` | enum | One story pattern (see **Story Pattern**). |
| `cta_style` | enum | One CTA style (see **CTA Style**). |

---

## Available Strategies

The engine may choose **only ONE**:

- Visual Demonstration
- Problem → Solution
- Before → After
- UGC Review
- POV
- Lifestyle
- Comparison
- Emotional Story
- Social Proof
- Authority

---

## Decision Rules

For every selection the `reason` field MUST explain:

1. **Why this strategy was selected** — grounded in the input signals.
2. **Why other strategies were rejected** — the runner-up strategies and why they
   lost.
3. **Expected business impact** — the outcome the strategy is expected to drive.
4. **Confidence score (0–100)** — mirrored in the `confidence` field.

**No hidden reasoning.** Every driver behind the selection is stated explicitly.

---

## Strategy Mapping Rules

The mapping rules are **extensible and declarative** — they describe *how signals
map to strategies*, not an implementation. New rules can be added without
changing the engine's contract.

### Signal Sources (compatibility with the Product Intelligence schema)

The abstract signals used by the rules map to concrete canonical fields:

| Signal | Source field(s) | Scale |
| --- | --- | --- |
| `demo_possible` | `visual_analysis.benefit_visually_demonstrable` | boolean |
| `visual_strength` | `visual_analysis.visual_proof_strength` | 0–100 |
| `problem_strength` | highest `pain_analysis[].severity` (top-ranked pain) | 0–100 |
| `emotion_strength` | Market Fit **Emotional Appeal** assessment; the Product Intelligence schema currently expresses emotion qualitatively via `customer_analysis.emotional_motivation` (see **Future Extension Points**) | 0–100 |

### Example rules (extensible)

```
IF demo_possible == true AND visual_strength >= 80
    → Prefer "Visual Demonstration"

IF emotion_strength >= 80
    → Prefer "Emotional Story"

IF problem_strength >= 80
    → Prefer "Problem → Solution"
```

Additional rules follow the same shape (condition → preferred strategy) and are
resolved by priority and confidence. The Market Fit Engine's
`recommended_strategy` acts as a prior that a rule may confirm or override, with
the override justified in `reason`.

---

## Hook Selection

Output exactly **one** hook category:

- Curiosity
- Shock
- Question
- Contrarian
- Transformation
- Demonstration
- Authority

The chosen `hook_type` must align with the selected strategy (for example,
`Visual Demonstration` pairs naturally with `Demonstration`; `Before → After`
with `Transformation`), and the alignment is stated in `reason`.

---

## Story Pattern

Output exactly **one** story pattern:

- Problem → Solution
- Before → After
- POV
- UGC
- Lifestyle
- Comparison

The `story_pattern` seeds the State Machine's `STORY_CREATED` state.

---

## CTA Style

Choose exactly **one**, and explain the selection in `reason`:

- **Direct** — a clear, explicit call to buy/act.
- **Soft** — a low-pressure invitation.
- **Urgency** — time- or scarcity-driven.
- **Curiosity** — invites the viewer to learn more.

---

## Decision Flow

```
Product Intelligence JSON ─┐
                           ├─►  CSE
Market Fit Result ─────────┘     │
   (decision != Reject)          │
                                 ▼
                 1. Derive signals (Signal Sources)
                                 ▼
                 2. Apply Strategy Mapping Rules  ──►  select ONE strategy
                                 ▼
                 3. Select hook_type aligned to strategy
                                 ▼
                 4. Select story_pattern
                                 ▼
                 5. Select cta_style
                                 ▼
                 6. Compute confidence + write full reason
                                 ▼
                     Output { strategy, reason, confidence,
                              hook_type, story_pattern, cta_style }
```

---

## Future Extension Points

- **Emotion score.** Add an explicit numeric emotion strength (e.g. a `scores`
  block) to the Product Intelligence schema so `emotion_strength` has a native
  0–100 source rather than being derived from Market Fit. Any such field must be
  added to the single canonical schema — never a second schema.
- **New strategies / hooks / patterns.** The enums are extension points; new
  values are added centrally and reflected here.
- **Rule packs.** Strategy Mapping Rules can grow into prioritized, versioned rule
  sets without changing the output contract.
- **Weighting.** Rule priority and confidence weighting are configuration, not
  part of this contract.

---

## Compatibility

| Requirement | How it is met |
| --- | --- |
| Product Intelligence schema | Inputs read canonical fields; the Signal Sources table maps every abstract signal to a real schema field. |
| Market Fit Engine | Consumes the Market Fit Result; gated on `decision != Reject`; reuses `recommended_strategy` / `recommended_hook_type` as priors. |
| State Machine | Realizes `STRATEGY_SELECTED` and `HOOK_SELECTED`; `story_pattern` seeds `STORY_CREATED`. |
| No duplicate architecture | No equivalent spec existed; the CSE fills a distinct role and references, rather than redefines, existing engines. |

---

## Scope Boundary

| In scope | Out of scope |
| --- | --- |
| Selecting one strategy, hook, story pattern, CTA | Generating advertisements |
| Declarative, extensible mapping rules | Implementing business logic |
| Explaining and scoring the selection | Writing prompts or creative |
| Feeding the State Machine's creative states | Rendering or delivery |
