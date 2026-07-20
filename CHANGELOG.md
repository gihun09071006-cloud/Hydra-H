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

## [v0.1] — Foundation

### Added

- Repository initialized with the HYDRA foundational structure.
- Core documentation: `README.md`, `HYDRA_SPEC.md`, `ROADMAP.md`, `CLAUDE.md`.
- Top-level folders (`docs/`, `system/`, `knowledge/`, `prompts/`,
  `automation/`, `data/`, `tests/`, `scripts/`, `examples/`, `assets/`), each
  with a purpose-defining `README.md`.
- License, `.gitignore`, and version history baseline.
