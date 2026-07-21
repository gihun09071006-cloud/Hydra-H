# HYDRA Prompt Compiler — Specification

## Purpose

The **Prompt Compiler** converts a validated storyboard into an AI video
generation prompt. It is the bridge between HYDRA's narrative layer and the
rendering backends that produce video.

The compiler is **model-agnostic**: it targets one backend at a time through a
common contract, and new backends can be added in the future without changing the
Story Engine or any upstream engine.

The Prompt Compiler defines *how a storyboard becomes a prompt payload*. It does
**not** implement prompt generation. This document is a specification only.

### Relationship to existing engines (no duplicate architecture)

No equivalent specification existed. The compiler occupies the stage between
storyboard and rendering:

| Concern | Owner |
| --- | --- |
| Producing the phased scene storyboard | Story Engine (`STORY_ENGINE.md`) |
| **Translating the storyboard into a backend prompt payload** | **Prompt Compiler (this doc)** |
| Understanding the product | Product Intelligence Engine (`PRODUCT_INTELLIGENCE_ENGINE.md`) |
| Ordering the pipeline via state | State Machine (`STATE_MACHINE.md`) |

The Prompt Compiler **realizes** the State Machine's `PROMPT_CREATED` state. Its
input is the Story Engine's validated output; its output is the render-ready
prompt payload that proceeds toward `QA_COMPLETED` and `READY_FOR_RENDER`.

---

## Inputs

### Input 1 — Validated Story Output

The Story Engine output (`system/STORY_ENGINE.md`): the validated storyboard
(`story_pattern`, `duration`, ordered `scenes[]`). The compiler consumes only a
storyboard that has passed Story Engine validation.

### Input 2 — Product Intelligence JSON

The canonical Product Intelligence Record
(`data/schemas/product_intelligence.schema.json`, documented in
`docs/PRODUCT_INTELLIGENCE.md`). It supplies product context (brand, product
name, USP, audience) used to enrich the prompt without altering the story.

---

## Outputs

The compiler emits a backend prompt payload:

```json
{
  "target_backend": "Higgsfield",
  "prompt": "",
  "negative_prompt": "",
  "metadata": {
    "duration": 20,
    "aspect_ratio": "9:16",
    "language": "",
    "version": "1.0"
  }
}
```

| Field | Type | Description |
| --- | --- | --- |
| `target_backend` | string | The rendering backend this payload targets (see **Supported Backends**). |
| `prompt` | string | The compiled, backend-specific prompt. |
| `negative_prompt` | string | Backend-specific negative prompt (what to avoid). |
| `metadata` | object | Render metadata. |
| `metadata.duration` | integer (seconds) | Total duration, carried unchanged from the storyboard. |
| `metadata.aspect_ratio` | string | Output aspect ratio, e.g. `9:16` for short-form vertical video. |
| `metadata.language` | string | Language of the prompt/output. |
| `metadata.version` | string | Compiler payload version. |

---

## Supported Backends

**Current**

- Higgsfield

**Future**

- Veo
- Runway
- Kling
- Pika

The architecture MUST allow adding a new backend **without changing the Story
Engine** (or any upstream engine). Backends are added at the compiler layer only.

---

## Compiler Rules

The Prompt Compiler:

- **consumes Story Engine output** — a validated storyboard.
- **never modifies the story** — it reads the storyboard; it does not rewrite,
  reorder, or re-time it.
- **translates narrative into backend-specific prompt format** — the same
  storyboard compiles to different payloads per backend.
- **preserves scene order** — scenes appear in the prompt in their storyboard
  order.
- **preserves timing** — scene and total durations are carried through unchanged.

---

## Compilation Flow

```
Validated Story Output ──┐
                         ├─►  Prompt Compiler
Product Intelligence JSON┘         │
                                   ▼
        1. Verify storyboard is present and validated
                                   ▼
        2. Select target_backend (default: Higgsfield)
                                   ▼
        3. Translate scenes (in order, with timing preserved) into the
           backend's prompt format; enrich with product context
                                   ▼
        4. Produce prompt + negative_prompt for the backend
                                   ▼
        5. Assemble metadata (duration, aspect_ratio, language, version)
                                   ▼
        6. Validate output completeness  ──►  missing? return validation failure
                                   ▼ (valid)
        Output { target_backend, prompt, negative_prompt, metadata }
```

---

## Validation

The compiler validates:

- **storyboard exists** — a validated Story Engine storyboard is present.
- **duration exists** — the total duration is present and carried into metadata.
- **backend exists** — `target_backend` is a supported backend.
- **prompt is generated** — a non-empty `prompt` is produced.
- **metadata is complete** — `duration`, `aspect_ratio`, `language`, and
  `version` are all present.

**If any requirement is missing, the compiler returns a validation failure** (it
does not emit an incomplete payload). This maps to the State Machine's
`PROMPT_CREATED` failure condition, which drives that state's retry / fallback.

### Validation Rules (summary)

| Rule | Requirement |
| --- | --- |
| Storyboard present | A validated storyboard is supplied. |
| Duration present | Total duration exists and is copied to `metadata.duration`. |
| Backend supported | `target_backend` is one of the supported backends. |
| Prompt produced | `prompt` is non-empty. |
| Metadata complete | All metadata fields are present. |
| Story integrity | Scene order and timing are unchanged from the storyboard. |

---

## Backend Extension Strategy

Adding a new backend is a compiler-only change:

1. **Register the backend** as a supported `target_backend` value.
2. **Add a backend adapter** — the translation from the common storyboard into
   that backend's prompt/negative-prompt format and its metadata conventions
   (e.g. aspect ratio, duration limits).
3. **Keep the contract stable** — the input (validated storyboard) and the output
   object shape do not change; only the adapter that fills `prompt`,
   `negative_prompt`, and backend-specific metadata is added.

Because backends live behind a common contract, the Story Engine and all upstream
engines remain untouched when a backend is added or removed. This is what makes
the compiler **model-agnostic**.

---

## Relationship Summary

| Engine / Stage | Relationship |
| --- | --- |
| **Story Engine** | Provides the validated storyboard — the compiler's primary input. The compiler never modifies it. |
| **Product Intelligence** | Supplies product context used to enrich the prompt without altering the story. |
| **State Machine** | The compiler realizes `PROMPT_CREATED`; validation failures drive its retry / fallback; output proceeds to `QA_COMPLETED`. |

---

## Compatibility

| Requirement | How it is met |
| --- | --- |
| Story Engine | Consumes the validated storyboard read-only; preserves scene order and timing. |
| Product Intelligence schema | Reads canonical product-context fields to enrich prompts; never redefines them. |
| State Machine | Realizes `PROMPT_CREATED`; validation maps to its failure condition; output feeds `QA_COMPLETED`. |
| Backend-agnostic architecture | Backends sit behind a common contract via adapters; adding one is a compiler-only change. |
| No duplicate specifications | No equivalent spec existed; the compiler fills a distinct role and references, rather than redefines, existing engines. |

---

## Scope Boundary

| In scope | Out of scope |
| --- | --- |
| Converting a storyboard into a backend prompt payload | Implementing prompt generation |
| Backend-agnostic contract + adapter strategy | Rendering the video |
| Preserving story order and timing | Modifying the story |
| Output validation | Backend API calls or delivery |
