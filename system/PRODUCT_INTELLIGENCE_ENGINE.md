# HYDRA Product Intelligence Engine (PIE) — Specification

The **Product Intelligence Engine (PIE)** is HYDRA's understanding layer. Its
job is to analyze a product *before any creative decision is made*.

> **Core principle — understand first.**
> PIE never starts by creating advertisements. It never writes prompts or
> creative. Its only output is a structured analysis of the product. The
> Decision Engine consumes that analysis; PIE itself produces no creative.

PIE is **rule-based**: every field is derived from explicit, deterministic
rules over the product's inputs. The same product and knowledge always produce
the same analysis.

The engine's output is expressed in **two synchronized formats**: this Markdown
schema (human-readable contract) and a JSON Schema (machine-readable contract,
`data/schemas/product_intelligence.schema.json`).

---

## 1. Position in the Pipeline

```
Product inputs  ──►  Product Intelligence Engine  ──►  Decision Engine  ──►  ...
                     (understand the product)          (decide the creative)
```

PIE sits at the front of the pipeline. It converts raw product information into
a complete **Product Intelligence Record**. It does not decide creative
direction (that is the Decision Engine, `DECISION_ENGINE.md`) and it does not
generate output.

---

## 2. Rule-Based Method

- **Deterministic.** Every scored or classified field follows a documented rule.
- **Evidence-bound.** A conclusion is only asserted from available product,
  category, and market inputs.
- **No generation.** PIE classifies and scores; it never authors creative.
- **Scored on a fixed scale.** All strength/potential fields use an integer
  **0–100** scale. All rankings are explicit and ordered.
- **Reproducible.** Identical inputs yield an identical Product Intelligence
  Record.

---

## 3. Output Schema

The Product Intelligence Record is composed of the following sections. Every
section is required.

### 3.1 Product Identity

| Field | Type | Description |
| --- | --- | --- |
| Product Name | string | The product's name. |
| Brand | string | The brand or seller. |
| Category | string | Product category / niche. |
| Price | object | `{ amount: number, currency: string }`. |
| Country | string | Target country (market). |
| Marketplace | string | Where it is sold (e.g. marketplace or channel). |

### 3.2 Functional Analysis

| Field | Type | Description |
| --- | --- | --- |
| Primary Function | string | The single core job the product does. |
| Secondary Functions | string[] | Additional jobs it performs. |
| Top 3 Features | string[3] | The three most advertising-relevant features. |
| Unique Selling Proposition (USP) | string | The one thing that sets it apart. |

### 3.3 Visual Analysis

| Field | Type | Description |
| --- | --- | --- |
| Benefit Visually Demonstrable | boolean | Can the benefit be shown on screen? |
| Visual Proof Strength | integer (0–100) | How strong the visual proof is. |
| Before/After Possible | boolean | Can a before/after be shown? |
| Transformation Possible | boolean | Can a transformation be shown? |

**Scoring rule — Visual Proof Strength (0–100):** higher when the benefit is
directly observable, produces an immediate visible change, and requires no
explanation to be understood. Lower when the benefit is abstract, delayed, or
must be described rather than seen.

### 3.4 Customer Analysis

| Field | Type | Description |
| --- | --- | --- |
| Primary Target | string | The main audience. |
| Secondary Target | string | The next-most-relevant audience. |
| Buying Situation | string | The context that triggers a purchase. |
| Daily Usage | string | How/when the product is used day to day. |
| Emotional Motivation | string | The emotional driver to buy. |
| Functional Motivation | string | The practical driver to buy. |

### 3.5 Pain Analysis

A ranked list of the customer's problems that the product addresses.

- Type: array of `{ problem: string, severity: integer (0–100), rank: integer }`.
- **Rule:** each pain is scored by severity (0–100) and the list is ordered by
  rank, most severe first (`rank = 1` is the most severe).

### 3.6 Objection Analysis

A ranked list of every plausible reason a customer would *not* buy.

- Type: array of `{ objection: string, probability: integer (0–100), rank: integer }`.
- **Rule:** each objection is scored by probability of occurring (0–100) and the
  list is ordered by rank, most probable first.

### 3.7 Competitive Analysis

| Field | Type | Description |
| --- | --- | --- |
| Existing Alternatives | string[] | Direct competing products. |
| Offline Alternative | string | What the customer could do offline instead. |
| DIY Alternative | string | What the customer could do themselves instead. |
| Why Buy This Instead | string | The reason to choose this over all alternatives. |

### 3.8 Virality Analysis

Five short-form potential dimensions, each scored **0–100**.

| Field | Type | Description |
| --- | --- | --- |
| Scroll Stop Potential | integer (0–100) | Likelihood of stopping the scroll. |
| Surprise Potential | integer (0–100) | Capacity to surprise the viewer. |
| Satisfaction Potential | integer (0–100) | Capacity to satisfy the viewer. |
| Shareability | integer (0–100) | Likelihood of being shared. |
| Comment Potential | integer (0–100) | Likelihood of driving comments. |

### 3.9 Platform Recommendation

Exactly **one** primary platform is selected.

| Field | Type | Description |
| --- | --- | --- |
| Primary Platform | enum | One of: `Instagram Reels`, `TikTok`, `YouTube Shorts`. |
| Reason | string | Why this platform, grounded in the analysis above. |

**Rule:** the recommendation is derived from the Virality Analysis, the target
audience (Customer Analysis), and the product category — the single platform
whose audience and format best match the product's strongest virality
dimensions is chosen. The reason must reference the evidence that led to it.

---

## 4. Output Formats

- **Markdown** — this document is the human-readable schema and rule contract.
- **JSON** — the machine-readable contract lives at
  `data/schemas/product_intelligence.schema.json` (JSON Schema), and every
  Product Intelligence Record PIE produces validates against it.

Both formats describe the same record. They must stay synchronized.

---

## 5. Scope Boundary

| In scope | Out of scope |
| --- | --- |
| Understanding and analyzing the product | Creating advertisements |
| Deterministic, rule-based scoring | Generating prompts or creative |
| Producing the Product Intelligence Record | Deciding creative direction |
| Recommending one platform, with reason | Channel delivery or automation |
