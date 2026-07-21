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
- ProductFacts JSON input mode: run the pipeline from a JSON file exported by
  the Coupang browser extension. The CLI gains `--facts-file` (mutually
  exclusive with URL and `--html-file` modes); `runtime/extension_facts.py`
  validates and maps the extension JSON onto the existing ProductFacts contract
  (seller→seller_name, image_urls[0]→main_image_url, product_url→source_url,
  affiliate_url preserved); `HydraPipeline.run_from_product_facts()` runs the
  same engine chain via a shared `_run_from_facts`. ProductFacts was extended
  (single contract, not duplicated) with source_url, affiliate_url, image_urls,
  product_id, item_id, rating, and review_count. Validation rejects missing
  file, invalid JSON, non-object JSON, missing product_name/product_url, bad
  price/image_urls types, and unsupported marketplace. Tests use the real
  extension-output shape; facts-file mode makes no network calls. No new schema
  or documentation.
- Real Anthropic Claude provider: `providers/claude/claude_provider.py`'s
  `ClaudeProvider` now calls the Anthropic Messages API (official SDK, one call
  per method, no retries/streaming/tools), parses strict JSON via a shared
  `providers/json_response_parser.py`, and returns the existing contracts
  (`ProductIntelligence`, `CreativeStrategy`, `Storyboard`, `RenderPrompt`). Four
  pure prompt builders live in `prompts/` (JSON-only, exact contract keys, no
  Markdown fences, null-over-invention, no chain-of-thought). The deterministic
  placeholder moved to `MockClaudeProvider`
  (`providers/claude/mock_claude_provider.py`). `ProviderFactory` selects by
  `HYDRA_AI_MODE` (default `mock`; `live` requires `ANTHROPIC_API_KEY`, no silent
  fallback); the pipeline's default provider is the mock so tests/local runs stay
  offline. Configuration (model default `claude-opus-4-8`, overridable via
  `ANTHROPIC_MODEL`) lives in one place; the API key is never logged, stored, or
  committed. Adds `anthropic` to `requirements.txt`. Tests cover the parser, the
  real provider via an injected fake client (contracts, one call, invalid JSON,
  missing key, no network), and mock/live factory selection.
- HYDRA Coupang browser extension MVP (`browser_extension/`): a Chrome
  Manifest V3 extension that extracts normalized product data from the Coupang
  product page open in the user's browser and downloads it as JSON. Minimal
  permissions (`activeTab`, `scripting`, `downloads`), host access restricted to
  Coupang only (no `<all_urls>`), and extraction gated to
  `…/vp/products/…` pages. It only reads the already-rendered DOM / JSON-LD /
  meta — no backend connection, automation, or anti-bot bypass. Output reuses
  the ProductFacts field names where they overlap. Tests
  (`tests/browser_extension/`) verify the MV3 structure, minimal permissions,
  Coupang-only hosts, and the normalized extraction contract. No new schema or
  documentation.
- Local Coupang HTML input mode: run HYDRA from a locally saved product-page
  HTML file when direct HTTP fetching is blocked (e.g. HTTP 403), without any
  anti-bot bypass. `HydraPipeline.run_from_html(html, source_url)` validates the
  source URL as a Coupang affiliate/product URL, rejects empty HTML, and reuses
  the same parser + engine chain as URL mode (shared `_run_from_html`). The CLI
  gains `--html-file` and `--source-url`: exactly one of URL mode or HTML mode,
  `--source-url` required with `--html-file`, UTF-8 file reading, and concise
  non-zero failures. The adapter adds `validate_source_url` reusing its existing
  strict validation. Tests cover both modes, argument errors, missing/empty
  files, invalid source domain, engine sequence, and no networking. No new
  schema or documentation.
- Real Coupang HTTP fetching (`adapters/coupang/coupang_adapter.py`):
  `CoupangAdapter.fetch()` now performs real HTTP via an injectable/mockable
  client (defaults to `requests`), replacing the placeholder. Accepts affiliate
  and direct product URLs, follows redirects, and returns raw product-page HTML
  with browser-like headers, an explicit timeout, and UTF-8 text. Security: only
  `link.coupang.com` / `www.coupang.com` / `coupang.com` may be requested;
  rejects non-HTTPS, non-Coupang, external or non-product redirect destinations,
  empty bodies, and non-HTML responses; validates both the original and final
  URLs. Descriptive adapter exceptions for invalid URL, timeout, connection,
  HTTP error, invalid redirect, non-HTML, and empty responses. Adds
  `requirements.txt` (requests). Runtime and CLI tests inject a mocked HTTP
  session (no real network). No new schema or documentation.
- HYDRA CLI runner (`hydra.py`): a command-line entry point that takes one
  Coupang URL (affiliate or direct product), creates the Claude placeholder
  provider via `ProviderFactory`, runs the existing `HydraPipeline`, and prints
  the returned RenderPrompt as indented UTF-8 JSON. Exit code 0 on success and
  non-zero on failure, with concise error messages on stderr (no tracebacks).
  Composition and user I/O only — no scraping, parsing, AI, or duplicated
  pipeline logic. Includes a comment marking the future publishing-compliance
  boundary (Coupang Partners disclosure enforced there, not on RenderPrompt).
  Tests (`tests/cli/test_hydra_cli.py`) cover accepted URLs, argument errors,
  invalid URL, JSON/contract output, failure exit codes, stderr, and no
  networking. No new schema or documentation.
- HYDRA runtime pipeline (`runtime/hydra_pipeline.py`): the application entry
  point. Given a Coupang URL (affiliate link or direct product URL) it runs the
  full pipeline — Adapter → Parser → ProductFacts → Product Intelligence Engine
  → Market Fit Engine → Creative Strategy Engine → Story Engine → Prompt Compiler
  Engine — and returns a `RenderPrompt`. Orchestration only; invalid URLs,
  intermediate contracts, or engine failures stop execution and propagate. The
  Coupang adapter gained `fetch()` / `is_affiliate_url()` so the adapter owns
  raw-source loading and redirect following (placeholder, no network). Tests
  (`tests/runtime/test_hydra_pipeline.py`) cover affiliate/direct URLs, engine
  order, provider calls, return type, invalid URL, exception propagation, and no
  networking. No new schema or documentation.
- Prompt Compiler Engine implementation (`engines/prompt_compiler_engine.py`):
  orchestration only — validates a `Storyboard` contract, delegates prompt
  compilation to the AI Provider (`provider.compile_prompt`), validates the
  returned `RenderPrompt` contract, and returns it. Contains no
  prompt-engineering, rendering, Higgsfield-specific, or networking logic. Unit
  tests (`tests/engines/test_prompt_compiler_engine.py`) cover valid input,
  invalid input, provider-called-once, return type, invalid provider output,
  exception propagation, and no networking. No new schema or documentation.
- Story Engine implementation (`engines/story_engine.py`): orchestration only —
  validates a `CreativeStrategy` contract, delegates storyboard generation to the
  AI Provider (`provider.generate_story`), validates the returned `Storyboard`
  contract, and returns it. Contains no prompt, storytelling/scene logic, or
  networking. Unit tests (`tests/engines/test_story_engine.py`) cover valid
  input, missing optional fields, invalid input, provider-called-once, return
  type, invalid provider output, exception propagation, and no networking. No
  new schema or documentation.
- Creative Strategy Engine implementation
  (`engines/creative_strategy_engine.py`): orchestration only — validates a
  `ProductIntelligence` contract and a Market Fit result, delegates the creative
  decision to the AI Provider (`provider.generate_creative_strategy`), validates
  the returned `CreativeStrategy` contract, and returns it. Contains no prompt,
  strategy logic, scoring, or networking. The provider interface's
  `generate_creative_strategy` was extended to accept the Market Fit result
  (backward-compatible default). Unit tests
  (`tests/engines/test_creative_strategy_engine.py`) cover valid inputs, missing
  optional fields, invalid inputs, provider-called-once, return type, invalid
  provider output, exception propagation, and no networking. No new schema or
  documentation.
- Product Intelligence Engine implementation
  (`engines/product_intelligence_engine.py`): orchestration only — validates a
  `ProductFacts` contract, delegates analysis to the configured AI Provider
  (`provider.analyze_product`), validates the result as a `ProductIntelligence`
  contract, and returns it. Contains no prompt, scoring, or networking. Unit
  tests (`tests/engines/test_product_intelligence_engine.py`) cover valid facts,
  missing optional fields, invalid facts, provider-called-once, return type,
  exception propagation, and no networking. No new schema or documentation.
- Internal AI contracts (`contracts/`): strongly typed Python dataclasses shared
  between Engines and Providers so a Provider never returns an arbitrary dict.
  Adds `ProductFacts`, `ProductIntelligence` (with nested identity/analysis
  types), `CreativeStrategy`, `Storyboard`, and `RenderPrompt`, each with
  `to_dict` / `from_dict` serialization and no external dependencies. Unit tests
  (`tests/contracts/test_contracts.py`) cover serialization, deserialization,
  equality, and default values. No documentation or schemas.
- AI provider abstraction (`providers/`): an interface layer so Engines never
  call a specific LLM directly. Adds the `AIProvider` base interface
  (`providers/base/provider.py`) with `analyze_product`,
  `generate_creative_strategy`, `generate_story`, and `compile_prompt`; a
  placeholder `ClaudeProvider` (`providers/claude/claude_provider.py`) returning
  deterministic mock responses with no networking, SDK, API keys, or randomness;
  and a `ProviderFactory` (`providers/factory.py`) that creates providers by
  name, raises `ValueError` for unknown names, and is extensible via
  `register`. Unit tests (`tests/providers/`) verify the factory, interface
  implementation, deterministic output, and absence of external calls. No new
  spec or schema.
- Product Intelligence Parser implementation (`parsers/product_parser.py`):
  converts a raw HTML string into a valid Product Intelligence object using HTML
  parsing only (no browser automation, external APIs, or network). Extracts
  product name, brand, price, currency, category, main image, description,
  features, and seller from JSON-LD and meta/markup, returning null/empty for
  missing values (never fabricated) and mapping onto the existing schema with
  neutral placeholders for non-extractable required fields. Acceptance tests
  (`tests/parsers/test_product_parser.py`) with an HTML fixture
  (`tests/fixtures/coupang_product_sample.html`) cover valid HTML, missing
  optional fields, invalid HTML, and schema validation. No new spec or schema.
- Market Fit Engine implementation (`engines/market_fit_engine.py`): executes
  the existing specification — consumes a Product Intelligence object and returns
  a Market Fit object (score, decision, strengths, weaknesses,
  recommended_strategy, recommended_hook_type, confidence). Deterministic scoring
  across the ten weighted categories with a written reason per score, and the
  decision thresholds from the spec. Unit tests
  (`tests/engines/test_market_fit_engine.py`) cover low / medium / high score
  products, the decision thresholds, and schema-valid output. No new
  specification or schema.
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
