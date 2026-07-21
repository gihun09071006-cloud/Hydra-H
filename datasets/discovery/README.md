# datasets/discovery/

Discovered product candidates for HYDRA.

## Purpose

This dataset holds the queue of **discovered products** — candidates HYDRA has
found and must decide about before any advertisement is created. Each record
conforms to the Product Discovery schema
(`data/schemas/product_discovery.schema.json`) and moves through the discovery
lifecycle (`discovered → analyzing → approved / rejected → published`).

This directory stores **data only**. It contains no scraping, no recommendation
logic, and no AI. How records are produced and evaluated is defined in
`system/PRODUCT_DISCOVERY.md`.

## Relationship to other datasets

- **`../products/`** — raw product information for products under analysis.
- **`../market_fit/`** — historical Market Fit evaluations that set the
  `market_fit_score` on a discovery record.
