# Changelog

All notable changes to HYDRA are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Advertising Decision Engine specification (`system/DECISION_ENGINE.md`):
  the eight-step decision workflow and the required structure for every
  decision (Reason, Confidence Score, Alternative Options, Expected Business
  Impact). Specification only — no implementation.
- Product Intelligence Engine (PIE) specification
  (`system/PRODUCT_INTELLIGENCE_ENGINE.md`): a rule-based, understand-first
  product analysis engine with a full output schema (Product Identity,
  Functional, Visual, Customer, Pain, Objection, Competitive, and Virality
  analysis, plus a single Platform Recommendation).
- PIE output contract as JSON Schema
  (`data/schemas/product_intelligence.schema.json`).
- HYDRA State Machine specification (`system/STATE_MACHINE.md`): the fixed
  nine-state campaign sequence (`INPUT_RECEIVED` → `READY_FOR_RENDER`) with a
  no-skip guarantee, and per-state contracts (Inputs, Outputs, Success/Failure
  Condition, Next/Previous State, Retry Logic).
- Market Fit Engine specification (`system/MARKET_FIT_ENGINE.md`): evaluates
  whether a product deserves creative production before any advertisement is
  generated, scoring ten weighted categories (max 100) with a written reason
  for every score, and mapping the total to a decision tier (Create
  Immediately / Priority A / Priority B / Optional / Reject).
- Market Fit output contract as JSON Schema
  (`data/schemas/market_fit.schema.json`).
- Dataset foundation (`datasets/` with `products/`, `winning_ads/`,
  `failed_ads/`, `patterns/`, `market_fit/`) and its `README.md`.
- Acceptance test structure (`tests/acceptance/README.md`) requiring at least
  one acceptance test per future engine.
- Winning Product dataset foundation: lets HYDRA learn from products that
  actually perform. Adds the Winning Product schema
  (`data/schemas/winning_product.schema.json`) capturing product identity,
  creative choices (hook type, story pattern, publish platform), and measured
  performance (views, likes, comments, shares, CTR, conversion rate, revenue)
  with a four-state lifecycle (testing, winner, loser, archived), and the
  research dataset (`datasets/research/README.md`) documenting its lifecycle and
  relationships to Product Discovery and performance learning. Dataset structure
  only — no scraping, recommendation logic, or AI.
- Product Discovery foundation: a data model deciding which product deserves an
  advertisement before any creative is generated. Adds the Product Discovery
  schema (`data/schemas/product_discovery.schema.json`) with the discovery
  record fields and a five-state status lifecycle (discovered, analyzing,
  approved, rejected, published), documentation (`system/PRODUCT_DISCOVERY.md`)
  covering the discovery workflow, product lifecycle, and relationships to the
  Product Adapter and Market Fit Engine, and the discovery dataset
  (`datasets/discovery/README.md`). Data model only — no scraping,
  recommendation logic, or AI.
- Coupang Product Adapter — HYDRA's first executable component. A marketplace
  adapter architecture (`adapters/base/product_adapter.py`) with the
  `ProductAdapter` interface (`validate`, `load`, `extract`,
  `to_product_intelligence`) and a placeholder Coupang adapter
  (`adapters/coupang/coupang_adapter.py`) that validates Coupang URLs and
  returns mock Product Intelligence — no scraping, browser automation, or
  external APIs. Includes an acceptance test
  (`tests/adapters/test_coupang_adapter.py`) validating the output against the
  Product Intelligence schema, and `requirements-dev.txt`.
- Prompt Compiler specification (`system/PROMPT_COMPILER.md`): a model-agnostic
  compiler that converts a validated storyboard into a backend prompt payload
  (`target_backend`, `prompt`, `negative_prompt`, `metadata`) without modifying
  the story, preserving scene order and timing. Documents the current
  (Higgsfield) and future (Veo, Runway, Kling, Pika) backends, a backend-only
  extension strategy, output validation, and compatibility with the Story
  Engine, Product Intelligence schema, and State Machine.
- Story Engine (SGE) specification (`system/STORY_ENGINE.md`): transforms the
  Creative Strategy output into a structured short-form storyboard of ordered
  scenes (duration, goal, description) across the five mandatory phases (Hook,
  Problem, Solution, Proof, CTA), with recommended timing, phase-completeness
  validation, and documented compatibility with the Creative Strategy Engine,
  Product Intelligence schema, and State Machine.
- Creative Strategy Engine (CSE) specification
  (`system/CREATIVE_STRATEGY_ENGINE.md`): selects the single best advertising
  strategy from the Product Intelligence Record and Market Fit Result, emitting
  one strategy plus hook type, story pattern, and CTA style with full reasoning
  and a 0–100 confidence. Includes declarative, extensible strategy-mapping
  rules with a signal-source table mapping to canonical schema fields, and
  documented compatibility with the Product Intelligence schema, Market Fit
  Engine, and State Machine.
- Product Intelligence schema documentation (`docs/PRODUCT_INTELLIGENCE.md`):
  documents every field of the single canonical schema
  (`data/schemas/product_intelligence.schema.json`) with purpose, type,
  example, required status, and consuming engine, plus a compatibility review
  against the Decision Engine, Market Fit Engine, and State Machine. Confirms a
  single source of truth — one Product Intelligence schema in the repository.

## [v0.1] — Foundation

### Added

- Repository initialized with the HYDRA foundational structure.
- Core documentation: `README.md`, `HYDRA_SPEC.md`, `ROADMAP.md`, `CLAUDE.md`.
- Top-level folders (`docs/`, `system/`, `knowledge/`, `prompts/`,
  `automation/`, `data/`, `tests/`, `scripts/`, `examples/`, `assets/`), each
  with a purpose-defining `README.md`.
- License, `.gitignore`, and version history baseline.
