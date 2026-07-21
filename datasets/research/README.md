# datasets/research/

Winning-product research records for HYDRA.

## Purpose

This dataset is how HYDRA **learns from products that actually perform**. Each
record captures a published product, the creative choices it ran with
(`hook_type`, `story_pattern`, `publish_platform`), and its measured outcomes
(`views`, `likes`, `comments`, `shares`, `ctr`, `conversion_rate`, `revenue`).
Records conform to `data/schemas/winning_product.schema.json`.

This directory stores **data only** — no scraping, no recommendation logic, and
no AI. It is the evidence base that future learning components draw on.

## Lifecycle

The `status` field moves through:

```
testing ──► winner
        └─► loser  ──► archived
```

| Status | Meaning |
| --- | --- |
| `testing` | Published and gathering performance data. |
| `winner` | Met the performance bar; a proven performer. |
| `loser` | Did not meet the bar. |
| `archived` | Retired from active research (winner or loser kept for history). |

## Relationship to Product Discovery

A winning-product record is the *outcome* side of a Product Discovery candidate.
Discovery (`system/PRODUCT_DISCOVERY.md`) tracks a product from `discovered` to
`published`; once published, its real-world performance is recorded here. The two
are linked by `product_id`, and share `marketplace`, `country`, `category`,
`product_url`, `price`, `currency`, and `market_fit_score`.

## Relationship to Performance Learning

This dataset is the input to HYDRA's **performance learning**: by comparing
`winner` and `loser` records, the system can distill which products, hooks, story
patterns, and platforms drive results. Those distilled signals are stored as
patterns in `datasets/patterns/`. This README defines the dataset only; the
learning logic is out of scope here.

## Not to be confused with

- **`../winning_ads/`** — successful *advertisements* (ad-creative level).
- **`../research/`** (this dataset) — *product-level* performance records.
