# Product Intelligence — Schema Documentation

This document describes the **single, canonical Product Intelligence schema** for
HYDRA.

- **Schema:** [`data/schemas/product_intelligence.schema.json`](../data/schemas/product_intelligence.schema.json)
- **Produced by:** the Product Intelligence Engine (`system/PRODUCT_INTELLIGENCE_ENGINE.md`)

> **Single source of truth.**
> There is exactly one Product Intelligence schema in the repository. Every
> downstream engine consumes this schema. No engine may redefine product fields.

Each field below is documented with its **Purpose**, **Type**, **Example**,
whether it is **Required**, and its **Consumers** — the engines that read it.

### Consumer legend

- **DE** — Advertising Decision Engine (`system/DECISION_ENGINE.md`)
- **MFE** — Market Fit Engine (`system/MARKET_FIT_ENGINE.md`)
- **SM** — State Machine (`system/STATE_MACHINE.md`)

> The **State Machine (SM)** carries the *entire* Product Intelligence Record as
> the artifact of its `PRODUCT_ANALYZED` state, so it consumes every field. The
> per-field Consumers column therefore highlights the **DE** and **MFE** fields
> that read each value directly; SM is implied for the whole record.

---

## `product_identity`  *(required)*

| Field | Purpose | Type | Example | Required | Consumers |
| --- | --- | --- | --- | --- | --- |
| `product_name` | The product's name. | string | `"Posture Corrector Pro"` | Required | DE |
| `brand` | The brand or seller. | string | `"FitAlign"` | Required | DE |
| `category` | Product category / niche. | string | `"Health & Fitness"` | Required | DE, MFE |
| `price.amount` | Numeric price. | number | `29.99` | Required | MFE (Price Advantage) |
| `price.currency` | ISO 4217 currency code. | string | `"USD"` | Required | MFE |
| `country` | Target market country. | string | `"United States"` | Required | DE |
| `marketplace` | Where the product is sold. | string | `"Amazon"` | Required | DE |

## `functional_analysis`  *(required)*

| Field | Purpose | Type | Example | Required | Consumers |
| --- | --- | --- | --- | --- | --- |
| `primary_function` | The single core job the product does. | string | `"Corrects posture"` | Required | DE |
| `secondary_functions` | Additional jobs it performs. | string[] | `["Relieves tension"]` | Required | DE |
| `top_features` | The three most advertising-relevant features. | string[3] | `["Adjustable straps","Breathable fabric","Discreet fit"]` | Required (exactly 3) | DE, MFE |
| `usp` | Unique Selling Proposition. | string | `"The only corrector with adaptive tension"` | Required | DE, MFE |

## `visual_analysis`  *(required)*

| Field | Purpose | Type | Example | Required | Consumers |
| --- | --- | --- | --- | --- | --- |
| `benefit_visually_demonstrable` | Can the benefit be shown on screen? | boolean | `true` | Required | MFE (Visual Demonstration), DE |
| `visual_proof_strength` | Strength of the visual proof. | integer (0–100) | `85` | Required | MFE |
| `before_after_possible` | Is a before/after possible? | boolean | `true` | Required | MFE, DE |
| `transformation_possible` | Is a transformation possible? | boolean | `false` | Required | MFE, DE |

## `customer_analysis`  *(required)*

| Field | Purpose | Type | Example | Required | Consumers |
| --- | --- | --- | --- | --- | --- |
| `primary_target` | The main audience. | string | `"Desk workers 25–45"` | Required | DE |
| `secondary_target` | The next-most-relevant audience. | string | `"Students"` | Required | DE |
| `buying_situation` | The context that triggers a purchase. | string | `"After a back-pain flare-up"` | Required | DE |
| `daily_usage` | How/when the product is used. | string | `"Worn 2–3 hours while working"` | Required | DE |
| `emotional_motivation` | The emotional driver to buy. | string | `"Relief and confidence"` | Required | DE, MFE (Emotional Appeal) |
| `functional_motivation` | The practical driver to buy. | string | `"Reduce daily back pain"` | Required | DE, MFE |

## `pain_analysis`  *(required, array — ranked by severity)*

Array of objects, ordered most-severe first (`rank = 1` is most severe).

| Field | Purpose | Type | Example | Required | Consumers |
| --- | --- | --- | --- | --- | --- |
| `problem` | A customer problem the product addresses. | string | `"Chronic back pain from sitting"` | Required | DE, MFE (Problem Severity) |
| `severity` | How severe the problem is. | integer (0–100) | `80` | Required | MFE |
| `rank` | Rank order of severity (1 = most severe). | integer (≥1) | `1` | Required | DE, MFE |

## `objection_analysis`  *(required, array — ranked by probability)*

Array of objects, ordered most-probable first (`rank = 1` is most probable).

| Field | Purpose | Type | Example | Required | Consumers |
| --- | --- | --- | --- | --- | --- |
| `objection` | A reason a customer might not buy. | string | `"Might be uncomfortable to wear"` | Required | DE |
| `probability` | Likelihood the objection occurs. | integer (0–100) | `60` | Required | DE |
| `rank` | Rank order of probability (1 = most probable). | integer (≥1) | `1` | Required | DE |

## `competitive_analysis`  *(required)*

| Field | Purpose | Type | Example | Required | Consumers |
| --- | --- | --- | --- | --- | --- |
| `existing_alternatives` | Direct competing products. | string[] | `["Generic posture braces"]` | Required | DE, MFE (Competition) |
| `offline_alternative` | What the customer could do offline instead. | string | `"Physical therapy"` | Required | DE, MFE |
| `diy_alternative` | What the customer could do themselves instead. | string | `"Posture exercises"` | Required | DE, MFE |
| `why_buy_this_instead` | The reason to choose this over alternatives. | string | `"Adaptive tension vs. fixed straps"` | Required | DE, MFE |

## `virality_analysis`  *(required)*

Each dimension is scored 0–100.

| Field | Purpose | Type | Example | Required | Consumers |
| --- | --- | --- | --- | --- | --- |
| `scroll_stop_potential` | Likelihood of stopping the scroll. | integer (0–100) | `75` | Required | MFE (Viral Potential), DE |
| `surprise_potential` | Capacity to surprise the viewer. | integer (0–100) | `60` | Required | MFE, DE |
| `satisfaction_potential` | Capacity to satisfy the viewer. | integer (0–100) | `70` | Required | MFE, DE |
| `shareability` | Likelihood of being shared. | integer (0–100) | `55` | Required | MFE, DE |
| `comment_potential` | Likelihood of driving comments. | integer (0–100) | `50` | Required | MFE, DE |

## `platform_recommendation`  *(required)*

| Field | Purpose | Type | Example | Required | Consumers |
| --- | --- | --- | --- | --- | --- |
| `primary_platform` | The single recommended platform. | enum: `Instagram Reels` \| `TikTok` \| `YouTube Shorts` | `"Instagram Reels"` | Required | DE, SM |
| `reason` | Why this platform, grounded in the analysis. | string | `"Highest scroll-stop fit for a visual health product"` | Required | DE, SM |

---

## Compatibility Review

The canonical schema was reviewed against every consuming engine. It is
**compatible with all three, and no field is missing**:

| Engine | How it consumes the schema | Result |
| --- | --- | --- |
| **Advertising Decision Engine** | Reads product, customer, motivation, objection, and competitive fields across its eight decision steps. | ✅ All required inputs present. |
| **Market Fit Engine** | Derives its scoring categories (Visual Demonstration, Problem Severity, Emotional Appeal, Price Advantage, Competition, Viral Potential, etc.) from the analytic fields above. | ✅ Source signals present; Market Fit produces its own scores. |
| **State Machine** | Carries the whole Product Intelligence Record as the output of its `PRODUCT_ANALYZED` state. | ✅ The record is the artifact it passes downstream. |

**Review outcome:** the existing schema is sufficient for all named consumers;
**no extension was required.** Should a future engine need a new product field,
it must be added to this one schema — never by creating a second schema.
