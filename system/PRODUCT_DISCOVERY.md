# HYDRA Product Discovery — Foundation

## Purpose

Product Discovery decides **what product deserves an advertisement** before any
creative is generated. It is the front door of HYDRA: it maintains a queue of
discovered product candidates and tracks each one through a lifecycle from first
sighting to published campaign.

This document defines the **data model and workflow only**. It contains **no
scraping, no recommendation logic, and no AI**. The data contract lives at
`data/schemas/product_discovery.schema.json`.

> **Note on schema location.** HYDRA keeps all JSON Schemas in one home,
> `data/schemas/`. The Product Discovery schema is placed there alongside
> `product_intelligence.schema.json` and `market_fit.schema.json` to keep a
> single schema directory (no duplicated architecture).

---

## Product Discovery Record

Each discovered product is a record with these fields:

| Field | Type | Description |
| --- | --- | --- |
| `product_id` | string | Stable HYDRA identifier for the product. |
| `marketplace` | string | Marketplace it was discovered on (e.g. Coupang). |
| `country` | string | Target market country. |
| `product_url` | string (URI) | Link to the listing; input to the marketplace adapter. |
| `category` | string | Product category / niche. |
| `price` | number | Numeric price. |
| `currency` | string | ISO 4217 currency code. |
| `estimated_margin` | number \| null | Estimated profit margin (0–100%). Null until estimated. |
| `market_fit_score` | integer \| null | Market Fit Engine score (0–100). Null until evaluated. |
| `discovery_source` | string | Where/how it was discovered. |
| `discovery_date` | string (date-time) | When it was discovered (ISO 8601). |
| `status` | enum | Lifecycle state (see below). |

---

## Product Lifecycle

The `status` field moves through five states:

```
discovered ──► analyzing ──► approved ──► published
                   │
                   └────────► rejected
```

| Status | Meaning |
| --- | --- |
| `discovered` | Newly found; not yet evaluated. `market_fit_score` is null. |
| `analyzing` | Being evaluated by the pipeline (adapter + Market Fit). |
| `approved` | Passed evaluation; cleared to enter creative production. |
| `rejected` | Did not pass evaluation; will not be advertised. |
| `published` | An advertisement has been produced and shipped. |

A product only advances to `approved` when its evaluation supports advertising;
otherwise it becomes `rejected`. The lifecycle never skips evaluation — nothing
reaches `published` without passing through `analyzing` and `approved`.

---

## Discovery Workflow

```
1. discover      A product is found and recorded  →  status = discovered
2. analyze       The marketplace adapter loads it into Product Intelligence,
                 and the Market Fit Engine scores it  →  status = analyzing
3. decide        Market Fit decision sets the outcome:
                    not Reject  →  status = approved
                    Reject      →  status = rejected
4. publish       Approved products proceed through the creative pipeline and,
                 once shipped, are marked  →  status = published
```

This document defines *when* each transition happens. It does not implement the
discovery or scoring logic.

---

## Relationship with the Product Adapter

- A discovery record's `product_url`, `marketplace`, `country`, `category`,
  `price`, and `currency` describe the listing that a **marketplace adapter**
  (`adapters/`, e.g. `CoupangAdapter`) consumes.
- During `analyzing`, the adapter's `analyze(url)` turns `product_url` into a
  Product Intelligence Record (`data/schemas/product_intelligence.schema.json`).
- Discovery records the *candidate*; the adapter produces the *understanding*.
  The two schemas are complementary and do not overlap.

## Relationship with the Market Fit Engine

- The **Market Fit Engine** (`system/MARKET_FIT_ENGINE.md`) evaluates the
  analyzed product and produces a `market_fit_score` (0–100) and a `decision`.
- That score is written back onto the discovery record's `market_fit_score`
  field, and the `decision` drives the `status` transition:
  a non-`Reject` decision → `approved`; a `Reject` decision → `rejected`.
- Historical evaluations are retained in `datasets/market_fit/`.

---

## Scope Boundary

| In scope | Out of scope |
| --- | --- |
| The Product Discovery data model | Scraping or fetching products |
| The status lifecycle and workflow | Recommendation / ranking logic |
| Relationships to adapter and Market Fit | AI or scoring implementation |
| One schema, one documentation file | Creative generation |
