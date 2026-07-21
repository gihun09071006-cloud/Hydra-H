# adapters/

Marketplace product adapters for HYDRA.

## Purpose

An adapter converts a marketplace product URL into a HYDRA **Product
Intelligence Record** (`data/schemas/product_intelligence.schema.json`). Adapters
are the entry point of the pipeline: they turn an external listing into the one
schema every downstream engine consumes.

## Structure

- **`base/`** — the `ProductAdapter` interface every marketplace adapter
  implements: `validate(url)`, `load(url)`, `extract()`, and
  `to_product_intelligence()`, orchestrated by `analyze(url)`.
- **`coupang/`** — the Coupang adapter (initial supported marketplace).

## Adding a marketplace

New marketplaces (AliExpress, Amazon, Rakuten, Temu, …) are added as a new
subpackage that subclasses `ProductAdapter`. Because every adapter emits the same
Product Intelligence contract, the core pipeline never changes when a marketplace
is added.
