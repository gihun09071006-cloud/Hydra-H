# HYDRA State Machine — Specification

Every HYDRA campaign moves through a fixed sequence of states. The state machine
guarantees that a campaign is processed in order, one state at a time, from raw
input to a render-ready package.

> **Core rule — no state may be skipped.**
> A campaign advances exactly one state at a time, in the defined order. A state
> is entered only after the previous state has met its success condition. There
> are no shortcuts, no jumps, and no reordering.

This document is a specification only. It defines the states and their
contracts; it contains **no implementation**.

---

## 1. State Sequence

```
INPUT_RECEIVED
    ↓
PRODUCT_ANALYZED
    ↓
STRATEGY_SELECTED
    ↓
HOOK_SELECTED
    ↓
STORY_CREATED
    ↓
SCENES_CREATED
    ↓
PROMPT_CREATED
    ↓
QA_COMPLETED
    ↓
READY_FOR_RENDER
```

`INPUT_RECEIVED` is the entry state. `READY_FOR_RENDER` is the terminal state
of this machine — the point at which the campaign is handed off to rendering.

---

## 2. Global Rules

- **Sequential only.** Transitions follow the sequence above; no state is skipped.
- **Forward on success.** A state advances to its Next State only when its
  Success Condition is met.
- **Backward on failure.** A state that fails and exhausts its retries returns to
  its Previous State (or halts at the entry state).
- **One state at a time.** A campaign occupies exactly one state at any moment.
- **Traceable.** Each transition records which state produced which output.
- **Deterministic contracts.** Every state has explicit inputs, outputs, and
  success/failure conditions defined below.

### 2.1 Transition Field Definitions

Each state is defined by the following fields:

| Field | Meaning |
| --- | --- |
| **Inputs** | What the state requires to begin. |
| **Outputs** | What the state produces on success. |
| **Success Condition** | What must be true to advance to the Next State. |
| **Failure Condition** | What causes the state to fail. |
| **Next State** | The state entered on success. |
| **Previous State** | The state returned to on unrecoverable failure. |
| **Retry Logic** | How failures are retried before falling back. |

---

## 3. State Definitions

### 3.1 INPUT_RECEIVED

- **Inputs:** Raw campaign request (product information, market, target country,
  marketplace, and any brief parameters).
- **Outputs:** A validated, normalized input package.
- **Success Condition:** Required input fields are present and valid.
- **Failure Condition:** Missing or malformed required input.
- **Next State:** `PRODUCT_ANALYZED`
- **Previous State:** — (entry state)
- **Retry Logic:** Reject and request corrected input; the campaign cannot
  proceed until valid input is received. No automatic backward transition
  (this is the entry point).

### 3.2 PRODUCT_ANALYZED

- **Inputs:** Validated input package from `INPUT_RECEIVED`.
- **Outputs:** A complete Product Intelligence Record (per the Product
  Intelligence Engine, `PRODUCT_INTELLIGENCE_ENGINE.md`).
- **Success Condition:** A valid, schema-conformant Product Intelligence Record
  is produced.
- **Failure Condition:** Analysis is incomplete or fails schema validation.
- **Next State:** `STRATEGY_SELECTED`
- **Previous State:** `INPUT_RECEIVED`
- **Retry Logic:** Retry the analysis up to a bounded number of attempts; on
  exhaustion, return to `INPUT_RECEIVED` for corrected or enriched input.

### 3.3 STRATEGY_SELECTED

- **Inputs:** Product Intelligence Record from `PRODUCT_ANALYZED`.
- **Outputs:** A selected marketing strategy, recorded as a decision (Reason,
  Confidence Score, Alternative Options, Expected Business Impact — per
  `DECISION_ENGINE.md`).
- **Success Condition:** One strategy is selected and its decision record is
  complete.
- **Failure Condition:** No viable strategy can be selected, or the decision
  record is incomplete.
- **Next State:** `HOOK_SELECTED`
- **Previous State:** `PRODUCT_ANALYZED`
- **Retry Logic:** Retry selection up to a bounded number of attempts; on
  exhaustion, return to `PRODUCT_ANALYZED` to re-examine the product.

### 3.4 HOOK_SELECTED

- **Inputs:** Selected strategy from `STRATEGY_SELECTED` and the Product
  Intelligence Record.
- **Outputs:** A selected hook (the opening angle that captures attention),
  recorded as a decision.
- **Success Condition:** One hook is selected with a complete decision record.
- **Failure Condition:** No hook aligns with the strategy, or the decision
  record is incomplete.
- **Next State:** `STORY_CREATED`
- **Previous State:** `STRATEGY_SELECTED`
- **Retry Logic:** Retry hook selection up to a bounded number of attempts; on
  exhaustion, return to `STRATEGY_SELECTED` to reconsider the strategy.

### 3.5 STORY_CREATED

- **Inputs:** Selected hook and strategy.
- **Outputs:** A structured story / narrative arc for the campaign.
- **Success Condition:** A coherent story is produced that is consistent with the
  hook and strategy.
- **Failure Condition:** The story is incoherent or inconsistent with upstream
  decisions.
- **Next State:** `SCENES_CREATED`
- **Previous State:** `HOOK_SELECTED`
- **Retry Logic:** Retry story construction up to a bounded number of attempts;
  on exhaustion, return to `HOOK_SELECTED`.

### 3.6 SCENES_CREATED

- **Inputs:** Story from `STORY_CREATED`.
- **Outputs:** An ordered set of scenes that decompose the story.
- **Success Condition:** The story is fully covered by a valid, ordered scene set.
- **Failure Condition:** Scenes are missing, out of order, or fail to cover the
  story.
- **Next State:** `PROMPT_CREATED`
- **Previous State:** `STORY_CREATED`
- **Retry Logic:** Retry scene breakdown up to a bounded number of attempts; on
  exhaustion, return to `STORY_CREATED`.

### 3.7 PROMPT_CREATED

- **Inputs:** Scene set from `SCENES_CREATED`.
- **Outputs:** Structured prompts for each scene (per the future Prompt Engine).
- **Success Condition:** Every scene has a complete, structured prompt.
- **Failure Condition:** One or more scenes lack a valid prompt.
- **Next State:** `QA_COMPLETED`
- **Previous State:** `SCENES_CREATED`
- **Retry Logic:** Retry prompt creation up to a bounded number of attempts; on
  exhaustion, return to `SCENES_CREATED`.

### 3.8 QA_COMPLETED

- **Inputs:** Prompts and all upstream artifacts.
- **Outputs:** A QA report validating schema conformance, brand consistency, and
  quality rules.
- **Success Condition:** All QA checks pass.
- **Failure Condition:** One or more QA checks fail.
- **Next State:** `READY_FOR_RENDER`
- **Previous State:** `PROMPT_CREATED`
- **Retry Logic:** On failure, return to the earliest state responsible for the
  failed check (bounded attempts), then re-run QA. On repeated exhaustion, halt
  and flag for review.

### 3.9 READY_FOR_RENDER

- **Inputs:** QA-approved campaign package.
- **Outputs:** A finalized, render-ready package handed off to rendering.
- **Success Condition:** The package is complete and marked ready.
- **Failure Condition:** The package is incomplete at hand-off.
- **Next State:** — (terminal state of this machine)
- **Previous State:** `QA_COMPLETED`
- **Retry Logic:** On failure, return to `QA_COMPLETED` for re-validation.

---

## 4. Retry & Fallback Model

- Each state retries its own work a **bounded** number of times before falling
  back to its Previous State.
- Fallback is always **one step backward** — the machine never jumps across
  multiple states, forward or backward.
- Repeated failure across retries and fallbacks **halts** the campaign and flags
  it for review rather than skipping a state.
- The exact retry counts and backoff policy are configuration, defined when the
  machine is implemented; this specification fixes only the structure.

---

## 5. Scope Boundary

| In scope | Out of scope |
| --- | --- |
| The state sequence and its ordering | Implementing the states |
| Each state's inputs, outputs, and conditions | Engine business logic |
| Transition, retry, and fallback rules | Rendering the campaign |
| The no-skip guarantee | Automation and delivery |
