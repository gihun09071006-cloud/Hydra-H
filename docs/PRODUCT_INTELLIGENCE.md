# Product Intelligence — Schema Documentation

This document defines the **official Product Intelligence schema** for HYDRA.

The schema lives at [`schemas/product_intelligence.schema.json`](../schemas/product_intelligence.schema.json)
and is the **single source of truth** for product fields across the entire
system.

> **Contract rules.**
> - Every downstream engine **must** consume this schema.
> - No engine may **redefine** product fields.
> - This schema is the **single source of truth**.

Each field below is documented with its **Purpose**, **Data Type**, **Example**,
and whether it is **Required** or **Optional**.

---

## `product`

Core product identity. **Required** (object).

| Field | Purpose | Data Type | Example | Required |
| --- | --- | --- | --- | --- |
| `name` | The product's name. | string | `"Posture Corrector Pro"` | Required |
| `brand` | The brand or seller. | string | `"FitAlign"` | Required |
| `category` | Product category / niche. | string | `"Health & Fitness"` | Required |
| `marketplace` | Where the product is sold. | string | `"Amazon"` | Required |
| `product_url` | Link to the product listing. | string (URI) | `"https://example.com/p/123"` | Optional |
| `price` | Numeric price of the product. | number | `29.99` | Required |
| `currency` | ISO 4217 currency code. | string | `"USD"` | Required |

---

## `features`

Concrete product features. **Required** (array of strings).

| Purpose | Data Type | Example | Required |
| --- | --- | --- | --- |
| The tangible attributes of the product. | string[] | `["Adjustable straps", "Breathable fabric"]` | Required |

---

## `benefits`

Customer-facing benefits derived from the features. **Required** (array of strings).

| Purpose | Data Type | Example | Required |
| --- | --- | --- | --- |
| What the customer gains from the features. | string[] | `["Reduces back pain", "Improves posture"]` | Required |

---

## `usp`

**Required** (string).

| Purpose | Data Type | Example | Required |
| --- | --- | --- | --- |
| Unique Selling Proposition — the one thing that sets the product apart. | string | `"The only corrector with adaptive tension"` | Required |

---

## `target_customer`

The intended audience. **Required** (object).

| Field | Purpose | Data Type | Example | Required |
| --- | --- | --- | --- | --- |
| `age_range` | Target age range. | string | `"25-34"` | Optional |
| `gender` | Target gender, or a neutral value where not applicable. | string | `"All"` | Optional |
| `persona` | Short description of the target customer persona. | string | `"Desk workers with chronic back strain"` | Required |

---

## `pain_points`

Customer problems the product addresses. **Required** (array of strings).

| Purpose | Data Type | Example | Required |
| --- | --- | --- | --- |
| The problems that motivate a purchase. | string[] | `["Back pain from sitting", "Poor posture"]` | Required |

---

## `objections`

Reasons a customer might hesitate to buy. **Required** (array of strings).

| Purpose | Data Type | Example | Required |
| --- | --- | --- | --- |
| The doubts that must be overcome to convert. | string[] | `["Might be uncomfortable", "Not sure it works"]` | Required |

---

## `visual_analysis`

Whether the product's value can be shown on screen. **Required** (object).

| Field | Purpose | Data Type | Example | Required |
| --- | --- | --- | --- | --- |
| `demo_possible` | Can the benefit be demonstrated on screen? | boolean | `true` | Required |
| `before_after` | Is a before/after comparison possible? | boolean | `true` | Required |
| `transformation` | Is a transformation possible? | boolean | `false` | Required |

---

## `scores`

Normalized 0–100 strength signals used by downstream engines. **Required** (object).

| Field | Purpose | Data Type | Example | Required |
| --- | --- | --- | --- | --- |
| `visual_strength` | Strength of the visual proof. | integer (0–100) | `85` | Required |
| `problem_strength` | Severity of the problem solved. | integer (0–100) | `70` | Required |
| `emotion_strength` | Strength of the emotional appeal. | integer (0–100) | `60` | Required |

---

## Compatibility

The Market Fit Engine (`system/MARKET_FIT_ENGINE.md`) consumes this Product
Intelligence contract as its input. The `scores` block (`visual_strength`,
`problem_strength`, `emotion_strength`) and the analytic fields above provide the
signals the Market Fit Engine scores against. Keeping this schema as the single
source of truth ensures every engine reads product data in exactly one shape.
